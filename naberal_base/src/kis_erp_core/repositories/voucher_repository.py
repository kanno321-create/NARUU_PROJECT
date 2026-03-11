"""
Voucher Repository
전표 CRUD (erp_vouchers + erp_voucher_items)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.voucher_models import VoucherFilter


class VoucherRepository:
    """전표 리포지토리"""

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in (
            "id", "voucher_id", "customer_id", "employee_id",
            "product_id", "bank_account_id",
        ):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    async def list(
        self,
        session: AsyncSession,
        filters: VoucherFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """
        전표 목록 조회

        Returns:
            List of Voucher dicts (items 미포함)
        """
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if filters.voucher_type is not None:
            where_clauses.append("v.voucher_type = :voucher_type")
            params["voucher_type"] = filters.voucher_type.value

        if filters.status is not None:
            where_clauses.append("v.status = :status")
            params["status"] = filters.status.value

        if filters.customer_id is not None:
            where_clauses.append("v.customer_id = :customer_id")
            params["customer_id"] = filters.customer_id

        if filters.start_date is not None:
            where_clauses.append("v.voucher_date >= :start_date")
            params["start_date"] = filters.start_date

        if filters.end_date is not None:
            where_clauses.append("v.voucher_date <= :end_date")
            params["end_date"] = filters.end_date

        if filters.search:
            where_clauses.append(
                "(v.voucher_no ILIKE :search OR v.memo ILIKE :search)"
            )
            params["search"] = f"%{filters.search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                v.id, v.voucher_no, v.voucher_type, v.voucher_date,
                v.customer_id, c.name AS customer_name,
                v.employee_id,
                v.supply_amount, v.tax_amount, v.total_amount,
                v.paid_amount, v.unpaid_amount,
                v.payment_method, v.bank_account_id,
                v.status, v.memo,
                v.created_at, v.updated_at
            FROM erp_vouchers v
            LEFT JOIN erp_customers c ON c.id = v.customer_id
            WHERE {where_sql}
            ORDER BY v.voucher_date DESC, v.voucher_no DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def get(self, session: AsyncSession, id: str) -> Optional[dict]:
        """전표 단일 조회 (items JOIN 포함)"""
        header_query = text("""
            SELECT
                v.id, v.voucher_no, v.voucher_type, v.voucher_date,
                v.customer_id, c.name AS customer_name,
                v.employee_id, e.name AS employee_name,
                v.supply_amount, v.tax_amount, v.total_amount,
                v.paid_amount, v.unpaid_amount,
                v.payment_method, v.bank_account_id,
                v.status, v.memo,
                v.created_at, v.updated_at
            FROM erp_vouchers v
            LEFT JOIN erp_customers c ON c.id = v.customer_id
            LEFT JOIN erp_employees e ON e.id = v.employee_id
            WHERE v.id = :id
        """)

        result = await session.execute(header_query, {"id": id})
        header_row = result.mappings().first()

        if not header_row:
            return None

        entry = self._row_to_dict(header_row)

        items_query = text("""
            SELECT
                vi.id, vi.voucher_id, vi.seq,
                vi.product_id, vi.product_name, vi.spec, vi.unit,
                vi.quantity, vi.unit_price, vi.supply_price,
                vi.tax_amount, vi.total_amount,
                vi.memo
            FROM erp_voucher_items vi
            WHERE vi.voucher_id = :id
            ORDER BY vi.seq ASC
        """)

        items_result = await session.execute(items_query, {"id": id})
        items_rows = items_result.mappings().all()

        entry["items"] = [self._row_to_dict(row) for row in items_rows]

        return entry

    async def create(
        self, session: AsyncSession, voucher_data: dict, items_data: List[dict]
    ) -> dict:
        """
        전표 생성 (header + items)

        Args:
            session: AsyncSession
            voucher_data: 전표 헤더 정보
            items_data: 전표 항목 목록 (supply_price/tax_amount/total_amount 계산 완료)

        Returns:
            Created Voucher dict with items
        """
        # 1. 전표번호 자동 생성
        no_query = text(
            "SELECT kis_beta.next_voucher_no(:vtype) AS voucher_no"
        )
        no_result = await session.execute(
            no_query, {"vtype": voucher_data["voucher_type"]}
        )
        voucher_no = no_result.mappings().first()["voucher_no"]

        # 2. 합계 계산
        supply_total = sum(item["supply_price"] for item in items_data)
        tax_total = sum(item["tax_amount"] for item in items_data)
        total = supply_total + tax_total

        # 3. 전표 헤더 생성
        header_query = text("""
            INSERT INTO erp_vouchers (
                id, voucher_no, voucher_type, voucher_date,
                customer_id, employee_id,
                supply_amount, tax_amount, total_amount,
                paid_amount, unpaid_amount,
                payment_method, bank_account_id,
                status, memo,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :voucher_no, :voucher_type, :voucher_date,
                :customer_id, :employee_id,
                :supply_amount, :tax_amount, :total_amount,
                0, :total_amount,
                :payment_method, :bank_account_id,
                'draft', :memo,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, voucher_no, voucher_type, voucher_date,
                customer_id, employee_id,
                supply_amount, tax_amount, total_amount,
                paid_amount, unpaid_amount,
                payment_method, bank_account_id,
                status, memo,
                created_at, updated_at
        """)

        header_result = await session.execute(header_query, {
            "voucher_no": voucher_no,
            "voucher_type": voucher_data["voucher_type"],
            "voucher_date": voucher_data["voucher_date"],
            "customer_id": voucher_data.get("customer_id"),
            "employee_id": voucher_data.get("employee_id"),
            "supply_amount": supply_total,
            "tax_amount": tax_total,
            "total_amount": total,
            "payment_method": voucher_data.get("payment_method"),
            "bank_account_id": voucher_data.get("bank_account_id"),
            "memo": voucher_data.get("memo"),
        })

        header_row = header_result.mappings().first()
        if not header_row:
            raise RuntimeError("Failed to create voucher")

        voucher = self._row_to_dict(header_row)
        voucher_id = voucher["id"]

        # 4. 전표 항목 생성
        items = await self._insert_items(session, voucher_id, items_data)
        voucher["items"] = items

        return voucher

    async def _insert_items(
        self, session: AsyncSession, voucher_id: str, items_data: List[dict]
    ) -> List[dict]:
        """전표 항목 일괄 생성"""
        items = []
        for idx, item in enumerate(items_data, 1):
            item_query = text("""
                INSERT INTO erp_voucher_items (
                    id, voucher_id, seq,
                    product_id, product_name, spec, unit,
                    quantity, unit_price, supply_price,
                    tax_amount, total_amount,
                    memo
                ) VALUES (
                    gen_random_uuid(), :voucher_id, :seq,
                    :product_id, :product_name, :spec, :unit,
                    :quantity, :unit_price, :supply_price,
                    :tax_amount, :total_amount,
                    :memo
                )
                RETURNING
                    id, voucher_id, seq,
                    product_id, product_name, spec, unit,
                    quantity, unit_price, supply_price,
                    tax_amount, total_amount,
                    memo
            """)

            item_result = await session.execute(item_query, {
                "voucher_id": voucher_id,
                "seq": idx,
                "product_id": item.get("product_id"),
                "product_name": item["product_name"],
                "spec": item.get("spec"),
                "unit": item.get("unit", "EA"),
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "supply_price": item["supply_price"],
                "tax_amount": item["tax_amount"],
                "total_amount": item["total_amount"],
                "memo": item.get("memo"),
            })

            item_row = item_result.mappings().first()
            if not item_row:
                raise RuntimeError("Failed to create voucher item")

            items.append(self._row_to_dict(item_row))

        return items

    async def update_header(
        self, session: AsyncSession, id: str, update_data: dict
    ) -> Optional[dict]:
        """전표 헤더 수정 (draft 상태만)"""
        set_clauses = ["updated_at = timezone('utc', now())"]
        params = {"id": id}

        field_map = {
            "voucher_date": "voucher_date",
            "customer_id": "customer_id",
            "employee_id": "employee_id",
            "payment_method": "payment_method",
            "bank_account_id": "bank_account_id",
            "memo": "memo",
            "supply_amount": "supply_amount",
            "tax_amount": "tax_amount",
            "total_amount": "total_amount",
            "unpaid_amount": "unpaid_amount",
        }

        for key, col in field_map.items():
            if key in update_data:
                set_clauses.append(f"{col} = :{key}")
                params[key] = update_data[key]

        set_sql = ", ".join(set_clauses)

        query = text(f"""
            UPDATE erp_vouchers
            SET {set_sql}
            WHERE id = :id AND status = 'draft'
            RETURNING
                id, voucher_no, voucher_type, voucher_date,
                customer_id, employee_id,
                supply_amount, tax_amount, total_amount,
                paid_amount, unpaid_amount,
                payment_method, bank_account_id,
                status, memo,
                created_at, updated_at
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_dict(row)

    async def delete_items(self, session: AsyncSession, voucher_id: str) -> None:
        """전표 항목 전체 삭제"""
        query = text("""
            DELETE FROM erp_voucher_items
            WHERE voucher_id = :voucher_id
        """)
        await session.execute(query, {"voucher_id": voucher_id})

    async def update_status(
        self, session: AsyncSession, id: str, status: str
    ) -> Optional[dict]:
        """전표 상태 변경"""
        query = text("""
            UPDATE erp_vouchers
            SET status = :status, updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING
                id, voucher_no, voucher_type, voucher_date,
                customer_id, employee_id,
                supply_amount, tax_amount, total_amount,
                paid_amount, unpaid_amount,
                payment_method, bank_account_id,
                status, memo,
                created_at, updated_at
        """)

        result = await session.execute(query, {"id": id, "status": status})
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_dict(row)

    async def delete(self, session: AsyncSession, id: str) -> bool:
        """전표 삭제 (draft 상태만, CASCADE로 items도 삭제)"""
        query = text("""
            DELETE FROM erp_vouchers
            WHERE id = :id AND status = 'draft'
            RETURNING id
        """)
        result = await session.execute(query, {"id": id})
        return result.mappings().first() is not None
