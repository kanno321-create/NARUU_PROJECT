"""
Order Repository
발주서 CRUD (erp_purchase_orders + erp_purchase_order_items)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional, List
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class OrderRepository:
    """발주서 리포지토리"""

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in (
            "id", "order_id", "supplier_id", "product_id",
        ):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    async def _generate_order_no(self, session: AsyncSession) -> str:
        """
        발주번호 자동 생성: PO-YYYYMMDD-NNNN

        당일 MAX order_no에서 시퀀스 추출 후 +1.
        당일 첫 발주면 0001부터 시작.
        """
        query = text("""
            SELECT MAX(order_no) AS max_no
            FROM erp_purchase_orders
            WHERE order_no LIKE 'PO-' || to_char(CURRENT_DATE, 'YYYYMMDD') || '-%'
        """)
        result = await session.execute(query)
        row = result.mappings().first()
        max_no = row["max_no"] if row else None

        if max_no:
            # PO-20260209-0003 → 0003 → 4
            seq = int(max_no.split("-")[-1]) + 1
        else:
            seq = 1

        date_query = text("SELECT to_char(CURRENT_DATE, 'YYYYMMDD') AS today")
        date_result = await session.execute(date_query)
        today = date_result.mappings().first()["today"]

        return f"PO-{today}-{seq:04d}"

    async def list(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """
        발주서 목록 조회 (items 미포함, supplier_name JOIN)

        Returns:
            List of Order dicts
        """
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if status is not None:
            where_clauses.append("o.status = :status")
            params["status"] = status

        if supplier_id is not None:
            where_clauses.append("o.supplier_id = :supplier_id")
            params["supplier_id"] = supplier_id

        if start_date is not None:
            where_clauses.append("o.order_date >= :start_date")
            params["start_date"] = start_date

        if end_date is not None:
            where_clauses.append("o.order_date <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                o.id, o.order_no, o.order_date,
                o.supplier_id, c.name AS supplier_name,
                o.delivery_date,
                o.total_amount, o.status, o.memo,
                o.created_at, o.updated_at
            FROM erp_purchase_orders o
            LEFT JOIN erp_customers c ON c.id = o.supplier_id
            WHERE {where_sql}
            ORDER BY o.order_date DESC, o.order_no DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def get(self, session: AsyncSession, order_id: str) -> Optional[dict]:
        """발주서 단일 조회 (items JOIN 포함)"""
        header_query = text("""
            SELECT
                o.id, o.order_no, o.order_date,
                o.supplier_id, c.name AS supplier_name,
                o.delivery_date,
                o.total_amount, o.status, o.memo,
                o.created_at, o.updated_at
            FROM erp_purchase_orders o
            LEFT JOIN erp_customers c ON c.id = o.supplier_id
            WHERE o.id = :id
        """)

        result = await session.execute(header_query, {"id": order_id})
        header_row = result.mappings().first()

        if not header_row:
            return None

        entry = self._row_to_dict(header_row)

        items_query = text("""
            SELECT
                i.id, i.order_id, i.seq,
                i.product_id, i.product_name, i.spec, i.unit,
                i.quantity, i.unit_price, i.amount,
                i.memo
            FROM erp_purchase_order_items i
            WHERE i.order_id = :order_id
            ORDER BY i.seq ASC
        """)

        items_result = await session.execute(items_query, {"order_id": order_id})
        items_rows = items_result.mappings().all()

        entry["items"] = [self._row_to_dict(row) for row in items_rows]

        return entry

    async def create(self, session: AsyncSession, data: dict) -> dict:
        """
        발주서 생성 (header + items)

        Args:
            session: AsyncSession
            data: 발주서 정보 (order_date, supplier_id, delivery_date, memo, items[])

        Returns:
            Created Order dict with items
        """
        # 1. 발주번호 자동 생성
        order_no = await self._generate_order_no(session)

        # 2. 항목별 금액 계산 + 합계
        items_data = data.get("items", [])
        total_amount = 0.0
        for item in items_data:
            amount = round(float(item.get("quantity", 1)) * float(item.get("unit_price", 0)), 2)
            item["amount"] = amount
            total_amount += amount

        # 3. 발주서 헤더 생성
        header_query = text("""
            INSERT INTO erp_purchase_orders (
                id, order_no, order_date,
                supplier_id, delivery_date,
                total_amount, status, memo,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :order_no, :order_date,
                :supplier_id, :delivery_date,
                :total_amount, 'draft', :memo,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, order_no, order_date,
                supplier_id, delivery_date,
                total_amount, status, memo,
                created_at, updated_at
        """)

        header_result = await session.execute(header_query, {
            "order_no": order_no,
            "order_date": data["order_date"],
            "supplier_id": data["supplier_id"],
            "delivery_date": data.get("delivery_date"),
            "total_amount": total_amount,
            "memo": data.get("memo"),
        })

        header_row = header_result.mappings().first()
        if not header_row:
            raise RuntimeError("발주서 생성 실패")

        order = self._row_to_dict(header_row)
        order_id = order["id"]

        # 4. 항목 생성
        items = await self._insert_items(session, order_id, items_data)
        order["items"] = items

        # 5. supplier_name 조회
        name_query = text("""
            SELECT name FROM erp_customers WHERE id = :supplier_id
        """)
        name_result = await session.execute(name_query, {"supplier_id": data["supplier_id"]})
        name_row = name_result.mappings().first()
        order["supplier_name"] = name_row["name"] if name_row else None

        return order

    async def _insert_items(
        self, session: AsyncSession, order_id: str, items_data: List[dict]
    ) -> List[dict]:
        """발주서 항목 일괄 생성"""
        items = []
        for idx, item in enumerate(items_data, 1):
            item_query = text("""
                INSERT INTO erp_purchase_order_items (
                    id, order_id, seq,
                    product_id, product_name, spec, unit,
                    quantity, unit_price, amount,
                    memo
                ) VALUES (
                    gen_random_uuid(), :order_id, :seq,
                    :product_id, :product_name, :spec, :unit,
                    :quantity, :unit_price, :amount,
                    :memo
                )
                RETURNING
                    id, order_id, seq,
                    product_id, product_name, spec, unit,
                    quantity, unit_price, amount,
                    memo
            """)

            item_result = await session.execute(item_query, {
                "order_id": order_id,
                "seq": idx,
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name", ""),
                "spec": item.get("spec"),
                "unit": item.get("unit", "EA"),
                "quantity": float(item.get("quantity", 1)),
                "unit_price": float(item.get("unit_price", 0)),
                "amount": float(item.get("amount", 0)),
                "memo": item.get("memo"),
            })

            item_row = item_result.mappings().first()
            if not item_row:
                raise RuntimeError("발주서 항목 생성 실패")

            items.append(self._row_to_dict(item_row))

        return items

    async def update(
        self, session: AsyncSession, order_id: str, data: dict
    ) -> Optional[dict]:
        """
        발주서 수정 (draft/sent 상태만)

        items가 제공되면: 기존 항목 전체 삭제 → 새 항목 생성 → 합계 재계산
        """
        # 1. 현재 상태 확인
        existing = await self.get(session, order_id)
        if not existing:
            return None

        if existing["status"] not in ("draft", "sent"):
            raise ValueError(
                f"수정할 수 없는 상태입니다: {existing['status']} "
                f"(draft 또는 sent만 수정 가능)"
            )

        # 2. 헤더 필드 업데이트 준비
        set_clauses = ["updated_at = timezone('utc', now())"]
        params: dict = {"id": order_id}

        field_map = {
            "order_date": "order_date",
            "supplier_id": "supplier_id",
            "delivery_date": "delivery_date",
            "memo": "memo",
        }

        for key, col in field_map.items():
            if key in data and data[key] is not None:
                set_clauses.append(f"{col} = :{key}")
                params[key] = data[key]

        # 3. 항목 교체 시 합계 재계산
        items_data = data.get("items")
        if items_data is not None:
            # 기존 항목 삭제
            delete_query = text("""
                DELETE FROM erp_purchase_order_items
                WHERE order_id = :order_id
            """)
            await session.execute(delete_query, {"order_id": order_id})

            # 금액 계산
            total_amount = 0.0
            for item in items_data:
                amount = round(float(item.get("quantity", 1)) * float(item.get("unit_price", 0)), 2)
                item["amount"] = amount
                total_amount += amount

            set_clauses.append("total_amount = :total_amount")
            params["total_amount"] = total_amount

            # 새 항목 생성
            await self._insert_items(session, order_id, items_data)

        set_sql = ", ".join(set_clauses)

        # 4. 헤더 업데이트
        query = text(f"""
            UPDATE erp_purchase_orders
            SET {set_sql}
            WHERE id = :id AND status IN ('draft', 'sent')
            RETURNING id
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        # 5. 전체 데이터 반환
        return await self.get(session, order_id)

    async def delete(self, session: AsyncSession, order_id: str) -> bool:
        """발주서 삭제 (draft 상태만, CASCADE로 items도 삭제)"""
        query = text("""
            DELETE FROM erp_purchase_orders
            WHERE id = :id AND status = 'draft'
            RETURNING id
        """)
        result = await session.execute(query, {"id": order_id})
        return result.mappings().first() is not None

    async def update_status(
        self, session: AsyncSession, order_id: str, new_status: str,
        memo_append: Optional[str] = None,
    ) -> Optional[dict]:
        """
        발주서 상태 변경 (전이 규칙 검증 포함)

        허용 전이:
        - draft → sent
        - sent → confirmed
        - confirmed → received
        - draft → cancelled
        - sent → cancelled
        """
        # 1. 전이 규칙 정의
        valid_transitions = {
            "draft": {"sent", "cancelled"},
            "sent": {"confirmed", "cancelled"},
            "confirmed": {"received"},
        }

        # 2. 현재 상태 조회
        current_query = text("""
            SELECT status FROM erp_purchase_orders WHERE id = :id
        """)
        current_result = await session.execute(current_query, {"id": order_id})
        current_row = current_result.mappings().first()

        if not current_row:
            return None

        current_status = current_row["status"]

        # 3. 전이 유효성 검증
        allowed = valid_transitions.get(current_status, set())
        if new_status not in allowed:
            raise ValueError(
                f"상태 변경 불가: {current_status} → {new_status}. "
                f"허용: {current_status} → {', '.join(sorted(allowed)) if allowed else '(없음)'}"
            )

        # 4. 상태 변경 (memo_append가 있으면 메모에 추가)
        if memo_append:
            query = text("""
                UPDATE erp_purchase_orders
                SET status = :new_status,
                    memo = CASE
                        WHEN memo IS NULL OR memo = '' THEN :memo_append
                        ELSE memo || E'\\n' || :memo_append
                    END,
                    updated_at = timezone('utc', now())
                WHERE id = :id
                RETURNING id
            """)
            params: dict = {
                "id": order_id,
                "new_status": new_status,
                "memo_append": memo_append,
            }
        else:
            query = text("""
                UPDATE erp_purchase_orders
                SET status = :new_status,
                    updated_at = timezone('utc', now())
                WHERE id = :id
                RETURNING id
            """)
            params = {"id": order_id, "new_status": new_status}

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        return await self.get(session, order_id)
