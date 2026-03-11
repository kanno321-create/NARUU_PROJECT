"""
Statement Repository
거래명세서 CRUD (erp_statements + erp_statement_vouchers)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class StatementRepository:
    """거래명세서 리포지토리"""

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in ("id", "customer_id", "statement_id", "voucher_id"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    async def list(
        self,
        session: AsyncSession,
        statement_type: Optional[str] = None,
        customer_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """
        거래명세서 목록 조회

        statement_type 필터: 테이블에 statement_type 컬럼이 없으므로
        연결된 전표(voucher)의 voucher_type으로 판별한다.
        - 'sales': 매출전표가 연결된 거래명세서
        - 'purchase': 매입전표가 연결된 거래명세서

        Returns:
            List of statement dicts with customer_name
        """
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if statement_type is not None:
            where_clauses.append("""
                EXISTS (
                    SELECT 1 FROM erp_statement_vouchers sv2
                    JOIN erp_vouchers v2 ON v2.id = sv2.voucher_id
                    WHERE sv2.statement_id = s.id
                      AND v2.voucher_type = :statement_type
                )
            """)
            params["statement_type"] = statement_type

        if customer_id is not None:
            where_clauses.append("s.customer_id = :customer_id")
            params["customer_id"] = customer_id

        if start_date is not None:
            where_clauses.append("s.statement_date >= :start_date")
            params["start_date"] = start_date

        if end_date is not None:
            where_clauses.append("s.statement_date <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                s.id, s.statement_no, s.statement_date,
                s.customer_id, c.name AS customer_name,
                s.supply_amount, s.tax_amount, s.total_amount,
                s.status, s.memo,
                s.created_at, s.updated_at
            FROM erp_statements s
            LEFT JOIN erp_customers c ON c.id = s.customer_id
            WHERE {where_sql}
            ORDER BY s.statement_date DESC, s.statement_no DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()

        statements = []
        for row in rows:
            entry = self._row_to_dict(row)
            # 연결된 voucher_id 목록 조회
            v_query = text("""
                SELECT voucher_id
                FROM erp_statement_vouchers
                WHERE statement_id = :sid
            """)
            v_result = await session.execute(v_query, {"sid": entry["id"]})
            v_rows = v_result.mappings().all()
            entry["voucher_ids"] = [str(r["voucher_id"]) for r in v_rows]
            statements.append(entry)

        return statements

    async def get(
        self, session: AsyncSession, statement_id: str
    ) -> Optional[dict]:
        """거래명세서 단일 조회 (연결된 voucher_ids 포함)"""
        query = text("""
            SELECT
                s.id, s.statement_no, s.statement_date,
                s.customer_id, c.name AS customer_name,
                s.supply_amount, s.tax_amount, s.total_amount,
                s.status, s.memo,
                s.created_at, s.updated_at
            FROM erp_statements s
            LEFT JOIN erp_customers c ON c.id = s.customer_id
            WHERE s.id = :id
        """)

        result = await session.execute(query, {"id": statement_id})
        row = result.mappings().first()

        if not row:
            return None

        entry = self._row_to_dict(row)

        # 연결된 voucher_id 목록 조회
        v_query = text("""
            SELECT voucher_id
            FROM erp_statement_vouchers
            WHERE statement_id = :sid
        """)
        v_result = await session.execute(v_query, {"sid": statement_id})
        v_rows = v_result.mappings().all()
        entry["voucher_ids"] = [str(r["voucher_id"]) for r in v_rows]

        return entry

    async def _generate_statement_no(
        self, session: AsyncSession, voucher_type: Optional[str]
    ) -> str:
        """
        거래명세서 번호 자동 생성

        패턴: SS-YYYYMMDD-NNNN (매출) / SP-YYYYMMDD-NNNN (매입)
        voucher_type이 없으면 기본 SS 사용
        """
        prefix = "SP" if voucher_type == "purchase" else "SS"
        date_str = datetime.utcnow().strftime("%Y%m%d")
        pattern = f"{prefix}-{date_str}-%"

        count_query = text("""
            SELECT COUNT(*) AS cnt
            FROM erp_statements
            WHERE statement_no LIKE :pattern
        """)
        count_result = await session.execute(count_query, {"pattern": pattern})
        cnt = count_result.mappings().first()["cnt"]
        seq = cnt + 1

        return f"{prefix}-{date_str}-{seq:04d}"

    async def _determine_voucher_type(
        self, session: AsyncSession, voucher_ids: List[str]
    ) -> Optional[str]:
        """연결된 전표들의 voucher_type을 확인하여 대표 타입 결정"""
        if not voucher_ids:
            return None

        query = text("""
            SELECT DISTINCT voucher_type
            FROM erp_vouchers
            WHERE id = ANY(:ids)
        """)
        result = await session.execute(query, {"ids": voucher_ids})
        rows = result.mappings().all()

        if not rows:
            return None

        types = [r["voucher_type"] for r in rows]
        if "purchase" in types:
            return "purchase"
        if "sales" in types:
            return "sales"
        return types[0]

    async def create(
        self, session: AsyncSession, data: dict
    ) -> dict:
        """
        거래명세서 생성 (header + voucher 연결)

        Args:
            data: {statement_date, customer_id, voucher_ids, memo}

        Returns:
            Created statement dict with voucher_ids
        """
        voucher_ids = data.get("voucher_ids", [])

        # 연결된 전표 타입으로 번호 접두사 결정
        voucher_type = await self._determine_voucher_type(session, voucher_ids)
        statement_no = await self._generate_statement_no(session, voucher_type)

        # 연결된 전표가 있으면 금액 합산
        supply_amount = 0.0
        tax_amount = 0.0
        total_amount = 0.0

        if voucher_ids:
            amounts_query = text("""
                SELECT
                    COALESCE(SUM(supply_amount), 0) AS supply_amount,
                    COALESCE(SUM(tax_amount), 0) AS tax_amount,
                    COALESCE(SUM(total_amount), 0) AS total_amount
                FROM erp_vouchers
                WHERE id = ANY(:ids)
            """)
            amounts_result = await session.execute(
                amounts_query, {"ids": voucher_ids}
            )
            amounts_row = amounts_result.mappings().first()
            supply_amount = float(amounts_row["supply_amount"])
            tax_amount = float(amounts_row["tax_amount"])
            total_amount = float(amounts_row["total_amount"])

        # INSERT statement header
        insert_query = text("""
            INSERT INTO erp_statements (
                id, statement_no, statement_date,
                customer_id,
                supply_amount, tax_amount, total_amount,
                status, memo,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :statement_no, :statement_date,
                :customer_id,
                :supply_amount, :tax_amount, :total_amount,
                'draft', :memo,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, statement_no, statement_date,
                customer_id,
                supply_amount, tax_amount, total_amount,
                status, memo,
                created_at, updated_at
        """)

        result = await session.execute(insert_query, {
            "statement_no": statement_no,
            "statement_date": data["statement_date"],
            "customer_id": data.get("customer_id"),
            "supply_amount": supply_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "memo": data.get("memo"),
        })

        header_row = result.mappings().first()
        if not header_row:
            raise RuntimeError("Failed to create statement")

        entry = self._row_to_dict(header_row)
        statement_id = entry["id"]

        # INSERT junction records
        for vid in voucher_ids:
            link_query = text("""
                INSERT INTO erp_statement_vouchers (statement_id, voucher_id)
                VALUES (:statement_id, :voucher_id)
            """)
            await session.execute(link_query, {
                "statement_id": statement_id,
                "voucher_id": vid,
            })

        entry["voucher_ids"] = voucher_ids

        # customer_name 조회
        if entry.get("customer_id"):
            name_query = text("""
                SELECT name FROM erp_customers WHERE id = :cid
            """)
            name_result = await session.execute(
                name_query, {"cid": entry["customer_id"]}
            )
            name_row = name_result.mappings().first()
            entry["customer_name"] = name_row["name"] if name_row else None
        else:
            entry["customer_name"] = None

        return entry

    async def create_from_voucher(
        self, session: AsyncSession, voucher_id: str
    ) -> Optional[dict]:
        """
        전표에서 거래명세서 자동 생성

        전표의 customer_id, 금액 정보를 읽어서 거래명세서를 생성하고
        해당 전표를 연결한다.

        Args:
            voucher_id: 원본 전표 ID

        Returns:
            Created statement dict, or None if voucher not found
        """
        # 전표 조회
        v_query = text("""
            SELECT
                id, voucher_type, voucher_date,
                customer_id,
                supply_amount, tax_amount, total_amount
            FROM erp_vouchers
            WHERE id = :vid
        """)
        v_result = await session.execute(v_query, {"vid": voucher_id})
        v_row = v_result.mappings().first()

        if not v_row:
            return None

        voucher_data = dict(v_row)
        voucher_type = voucher_data["voucher_type"]

        # 거래명세서 번호 생성
        statement_no = await self._generate_statement_no(session, voucher_type)

        # INSERT statement header
        insert_query = text("""
            INSERT INTO erp_statements (
                id, statement_no, statement_date,
                customer_id,
                supply_amount, tax_amount, total_amount,
                status, memo,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :statement_no, :statement_date,
                :customer_id,
                :supply_amount, :tax_amount, :total_amount,
                'draft', NULL,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, statement_no, statement_date,
                customer_id,
                supply_amount, tax_amount, total_amount,
                status, memo,
                created_at, updated_at
        """)

        result = await session.execute(insert_query, {
            "statement_no": statement_no,
            "statement_date": voucher_data["voucher_date"],
            "customer_id": str(voucher_data["customer_id"]) if voucher_data["customer_id"] else None,
            "supply_amount": float(voucher_data["supply_amount"] or 0),
            "tax_amount": float(voucher_data["tax_amount"] or 0),
            "total_amount": float(voucher_data["total_amount"] or 0),
        })

        header_row = result.mappings().first()
        if not header_row:
            raise RuntimeError("Failed to create statement from voucher")

        entry = self._row_to_dict(header_row)
        statement_id = entry["id"]

        # 전표-거래명세서 연결
        link_query = text("""
            INSERT INTO erp_statement_vouchers (statement_id, voucher_id)
            VALUES (:statement_id, :voucher_id)
        """)
        await session.execute(link_query, {
            "statement_id": statement_id,
            "voucher_id": voucher_id,
        })

        entry["voucher_ids"] = [str(voucher_data["id"])]

        # customer_name 조회
        if entry.get("customer_id"):
            name_query = text("""
                SELECT name FROM erp_customers WHERE id = :cid
            """)
            name_result = await session.execute(
                name_query, {"cid": entry["customer_id"]}
            )
            name_row = name_result.mappings().first()
            entry["customer_name"] = name_row["name"] if name_row else None
        else:
            entry["customer_name"] = None

        return entry

    async def update(
        self, session: AsyncSession, statement_id: str, data: dict
    ) -> Optional[dict]:
        """
        거래명세서 수정 (draft 상태만)

        Args:
            statement_id: 거래명세서 ID
            data: {statement_date?, customer_id?, voucher_ids?, memo?}

        Returns:
            Updated statement dict, or None if not found / not draft
        """
        set_clauses = ["updated_at = timezone('utc', now())"]
        params: dict = {"id": statement_id}

        field_map = {
            "statement_date": "statement_date",
            "customer_id": "customer_id",
            "memo": "memo",
        }

        for key, col in field_map.items():
            if key in data and data[key] is not None:
                set_clauses.append(f"{col} = :{key}")
                params[key] = data[key]

        # voucher_ids가 변경되면 금액도 재계산
        voucher_ids = data.get("voucher_ids")
        if voucher_ids is not None:
            # 기존 연결 삭제
            del_query = text("""
                DELETE FROM erp_statement_vouchers
                WHERE statement_id = :sid
            """)
            await session.execute(del_query, {"sid": statement_id})

            # 새 연결 생성
            for vid in voucher_ids:
                link_query = text("""
                    INSERT INTO erp_statement_vouchers (statement_id, voucher_id)
                    VALUES (:statement_id, :voucher_id)
                """)
                await session.execute(link_query, {
                    "statement_id": statement_id,
                    "voucher_id": vid,
                })

            # 금액 재계산
            if voucher_ids:
                amounts_query = text("""
                    SELECT
                        COALESCE(SUM(supply_amount), 0) AS supply_amount,
                        COALESCE(SUM(tax_amount), 0) AS tax_amount,
                        COALESCE(SUM(total_amount), 0) AS total_amount
                    FROM erp_vouchers
                    WHERE id = ANY(:ids)
                """)
                amounts_result = await session.execute(
                    amounts_query, {"ids": voucher_ids}
                )
                amounts_row = amounts_result.mappings().first()
                set_clauses.append("supply_amount = :supply_amount")
                set_clauses.append("tax_amount = :tax_amount")
                set_clauses.append("total_amount = :total_amount")
                params["supply_amount"] = float(amounts_row["supply_amount"])
                params["tax_amount"] = float(amounts_row["tax_amount"])
                params["total_amount"] = float(amounts_row["total_amount"])
            else:
                set_clauses.append("supply_amount = 0")
                set_clauses.append("tax_amount = 0")
                set_clauses.append("total_amount = 0")

        set_sql = ", ".join(set_clauses)

        query = text(f"""
            UPDATE erp_statements
            SET {set_sql}
            WHERE id = :id AND status = 'draft'
            RETURNING
                id, statement_no, statement_date,
                customer_id,
                supply_amount, tax_amount, total_amount,
                status, memo,
                created_at, updated_at
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        entry = self._row_to_dict(row)

        # voucher_ids 조회
        v_query = text("""
            SELECT voucher_id
            FROM erp_statement_vouchers
            WHERE statement_id = :sid
        """)
        v_result = await session.execute(v_query, {"sid": statement_id})
        v_rows = v_result.mappings().all()
        entry["voucher_ids"] = [str(r["voucher_id"]) for r in v_rows]

        # customer_name 조회
        if entry.get("customer_id"):
            name_query = text("""
                SELECT name FROM erp_customers WHERE id = :cid
            """)
            name_result = await session.execute(
                name_query, {"cid": entry["customer_id"]}
            )
            name_row = name_result.mappings().first()
            entry["customer_name"] = name_row["name"] if name_row else None
        else:
            entry["customer_name"] = None

        return entry

    async def delete(
        self, session: AsyncSession, statement_id: str
    ) -> bool:
        """
        거래명세서 삭제 (draft 상태만, CASCADE로 junction도 삭제)

        Returns:
            True if deleted, False if not found or not draft
        """
        query = text("""
            DELETE FROM erp_statements
            WHERE id = :id AND status = 'draft'
            RETURNING id
        """)
        result = await session.execute(query, {"id": statement_id})
        deleted = result.mappings().first() is not None
        return deleted
