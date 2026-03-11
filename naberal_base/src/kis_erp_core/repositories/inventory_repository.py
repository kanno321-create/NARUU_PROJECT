"""
Inventory Repository
재고현황/재고조정/재고이동 CRUD (erp_products + erp_stock_adjustments + erp_inventory_movements)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional, List
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class InventoryRepository:
    """재고 리포지토리"""

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in (
            "id", "product_id", "employee_id", "voucher_id",
        ):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    # ==================== 재고 현황 ====================

    async def list_status(
        self,
        session: AsyncSession,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """
        재고현황 목록 조회 (erp_products 기반)

        Args:
            session: AsyncSession
            category: 카테고리 필터
            low_stock_only: True면 stock_qty <= min_stock인 것만
            skip: offset
            limit: limit

        Returns:
            List of inventory status dicts
        """
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if category is not None:
            where_clauses.append("p.category = :category")
            params["category"] = category

        if low_stock_only:
            where_clauses.append("p.stock_qty <= p.min_stock")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                p.id AS product_id,
                p.code AS product_code,
                p.name AS product_name,
                p.category,
                p.unit,
                COALESCE(p.stock_qty, 0) AS quantity,
                COALESCE(p.unit_cost, 0) AS unit_cost,
                COALESCE(p.stock_qty, 0) * COALESCE(p.unit_cost, 0) AS total_cost,
                COALESCE(p.min_stock, 0) AS min_stock,
                CASE
                    WHEN COALESCE(p.stock_qty, 0) <= COALESCE(p.min_stock, 0) THEN true
                    ELSE false
                END AS is_low_stock
            FROM erp_products p
            WHERE {where_sql}
            ORDER BY p.name ASC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def get_product_status(
        self,
        session: AsyncSession,
        product_id: str,
    ) -> Optional[dict]:
        """
        단일 상품 재고현황 조회

        Args:
            session: AsyncSession
            product_id: 상품 UUID

        Returns:
            Inventory status dict or None
        """
        query = text("""
            SELECT
                p.id AS product_id,
                p.code AS product_code,
                p.name AS product_name,
                p.category,
                p.unit,
                COALESCE(p.stock_qty, 0) AS quantity,
                COALESCE(p.unit_cost, 0) AS unit_cost,
                COALESCE(p.stock_qty, 0) * COALESCE(p.unit_cost, 0) AS total_cost,
                COALESCE(p.min_stock, 0) AS min_stock,
                CASE
                    WHEN COALESCE(p.stock_qty, 0) <= COALESCE(p.min_stock, 0) THEN true
                    ELSE false
                END AS is_low_stock
            FROM erp_products p
            WHERE p.id = :product_id
        """)

        result = await session.execute(query, {"product_id": product_id})
        row = result.mappings().first()
        if not row:
            return None
        return self._row_to_dict(row)

    async def get_summary(self, session: AsyncSession) -> dict:
        """
        재고현황 요약 집계

        Returns:
            dict with total_products, total_value, low_stock_count, out_of_stock_count
        """
        query = text("""
            SELECT
                COUNT(*)::int AS total_products,
                COALESCE(SUM(COALESCE(stock_qty, 0) * COALESCE(unit_cost, 0)), 0) AS total_value,
                COUNT(*) FILTER (
                    WHERE COALESCE(stock_qty, 0) > 0
                      AND COALESCE(stock_qty, 0) <= COALESCE(min_stock, 0)
                )::int AS low_stock_count,
                COUNT(*) FILTER (
                    WHERE COALESCE(stock_qty, 0) <= 0
                )::int AS out_of_stock_count
            FROM erp_products
        """)

        result = await session.execute(query)
        row = result.mappings().first()
        if not row:
            return {
                "total_products": 0,
                "total_value": 0,
                "low_stock_count": 0,
                "out_of_stock_count": 0,
            }
        return dict(row)

    # ==================== 재고 조정 ====================

    async def _generate_adjustment_no(self, session: AsyncSession) -> str:
        """
        재고조정번호 자동 생성: ADJ-YYYYMMDD-NNNN

        당일 MAX adjustment_no에서 시퀀스 추출 후 +1.
        당일 첫 조정이면 0001부터 시작.
        """
        query = text("""
            SELECT MAX(adjustment_no) AS max_no
            FROM erp_stock_adjustments
            WHERE adjustment_no LIKE 'ADJ-' || to_char(CURRENT_DATE, 'YYYYMMDD') || '-%'
        """)
        result = await session.execute(query)
        row = result.mappings().first()
        max_no = row["max_no"] if row else None

        if max_no:
            seq = int(max_no.split("-")[-1]) + 1
        else:
            seq = 1

        date_query = text("SELECT to_char(CURRENT_DATE, 'YYYYMMDD') AS today")
        date_result = await session.execute(date_query)
        today = date_result.mappings().first()["today"]

        return f"ADJ-{today}-{seq:04d}"

    async def list_adjustments(
        self,
        session: AsyncSession,
        product_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """
        재고조정 내역 조회

        Args:
            session: AsyncSession
            product_id: 상품 ID 필터
            start_date: 시작일 필터
            end_date: 종료일 필터
            skip: offset
            limit: limit

        Returns:
            List of adjustment dicts with product info
        """
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if product_id is not None:
            where_clauses.append("a.product_id = :product_id")
            params["product_id"] = product_id

        if start_date is not None:
            where_clauses.append("a.adjustment_date >= :start_date")
            params["start_date"] = start_date

        if end_date is not None:
            where_clauses.append("a.adjustment_date <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                a.id,
                a.adjustment_no,
                a.adjustment_date,
                a.adjustment_type,
                a.product_id,
                p.code AS product_code,
                p.name AS product_name,
                COALESCE(a.before_qty, 0) AS before_quantity,
                a.adjustment_qty AS adjustment_quantity,
                COALESCE(a.after_qty, 0) AS after_quantity,
                a.reason,
                a.memo,
                a.employee_id,
                a.created_at
            FROM erp_stock_adjustments a
            LEFT JOIN erp_products p ON p.id = a.product_id
            WHERE {where_sql}
            ORDER BY a.adjustment_date DESC, a.adjustment_no DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def create_adjustment(
        self, session: AsyncSession, data: dict
    ) -> dict:
        """
        재고조정 등록

        1. 현재 재고 수량 조회 (erp_products.stock_qty)
        2. adjustment_type에 따라 after_qty 계산
        3. adjustment_no 자동 생성 (ADJ-YYYYMMDD-NNNN)
        4. erp_stock_adjustments INSERT
        5. erp_inventory_movements INSERT (DB trigger가 stock_qty 갱신)
        6. 생성된 조정 내역 반환

        Args:
            session: AsyncSession
            data: dict with adjustment_date, adjustment_type, product_id,
                  adjustment_quantity, reason, memo (optional)

        Returns:
            Created adjustment dict with product info
        """
        product_id = data["product_id"]
        adjustment_type = data["adjustment_type"]
        adjustment_qty = float(data["adjustment_quantity"])

        # 1. 현재 재고 수량 조회
        stock_query = text("""
            SELECT COALESCE(stock_qty, 0) AS stock_qty
            FROM erp_products
            WHERE id = :product_id
        """)
        stock_result = await session.execute(stock_query, {"product_id": product_id})
        stock_row = stock_result.mappings().first()
        if not stock_row:
            raise ValueError(f"상품 ID '{product_id}'을(를) 찾을 수 없습니다")

        before_qty = float(stock_row["stock_qty"])

        # 2. after_qty 계산
        if adjustment_type == "increase":
            after_qty = before_qty + adjustment_qty
        elif adjustment_type == "decrease":
            after_qty = max(0, before_qty - adjustment_qty)
        elif adjustment_type == "set":
            after_qty = adjustment_qty
        else:
            raise ValueError(
                f"유효하지 않은 조정유형: {adjustment_type} "
                f"(increase/decrease/set만 허용)"
            )

        # 3. 조정번호 자동 생성
        adjustment_no = await self._generate_adjustment_no(session)

        # 4. erp_stock_adjustments INSERT
        adj_query = text("""
            INSERT INTO erp_stock_adjustments (
                id, adjustment_no, adjustment_date,
                adjustment_type, product_id,
                before_qty, adjustment_qty, after_qty,
                reason, employee_id, memo,
                created_at
            ) VALUES (
                gen_random_uuid(), :adjustment_no, :adjustment_date,
                :adjustment_type, :product_id,
                :before_qty, :adjustment_qty, :after_qty,
                :reason, :employee_id, :memo,
                timezone('utc', now())
            )
            RETURNING
                id, adjustment_no, adjustment_date,
                adjustment_type, product_id,
                before_qty AS before_quantity,
                adjustment_qty AS adjustment_quantity,
                after_qty AS after_quantity,
                reason, employee_id, memo,
                created_at
        """)

        adj_result = await session.execute(adj_query, {
            "adjustment_no": adjustment_no,
            "adjustment_date": data["adjustment_date"],
            "adjustment_type": adjustment_type,
            "product_id": product_id,
            "before_qty": before_qty,
            "adjustment_qty": adjustment_qty,
            "after_qty": after_qty,
            "reason": data["reason"],
            "employee_id": data.get("employee_id"),
            "memo": data.get("memo"),
        })

        adj_row = adj_result.mappings().first()
        if not adj_row:
            raise RuntimeError("재고조정 생성 실패")

        adjustment = self._row_to_dict(adj_row)

        # 5. erp_inventory_movements INSERT (DB trigger가 stock_qty 갱신)
        movement_query = text("""
            INSERT INTO erp_inventory_movements (
                id, movement_date, movement_type,
                product_id, quantity, unit_cost,
                reason, before_qty, after_qty,
                created_at
            ) VALUES (
                gen_random_uuid(), :movement_date, 'adjust',
                :product_id, :quantity, NULL,
                :reason, :before_qty, :after_qty,
                timezone('utc', now())
            )
        """)

        # movement quantity: 실제 변동량 (양수/음수 무관, DB trigger가 after_qty 기준으로 처리)
        movement_qty = after_qty - before_qty

        await session.execute(movement_query, {
            "movement_date": data["adjustment_date"],
            "product_id": product_id,
            "quantity": abs(movement_qty),
            "reason": f"[재고조정] {adjustment_no}: {data['reason']}",
            "before_qty": before_qty,
            "after_qty": after_qty,
        })

        # 6. 상품 정보 JOIN 반환
        product_query = text("""
            SELECT code AS product_code, name AS product_name
            FROM erp_products
            WHERE id = :product_id
        """)
        product_result = await session.execute(product_query, {"product_id": product_id})
        product_row = product_result.mappings().first()
        if product_row:
            adjustment["product_code"] = product_row["product_code"]
            adjustment["product_name"] = product_row["product_name"]

        return adjustment

    # ==================== 재고 이동 ====================

    async def list_movements(
        self,
        session: AsyncSession,
        product_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """
        재고이동 내역 조회 (입출고 + 조정)

        Args:
            session: AsyncSession
            product_id: 상품 ID 필터
            movement_type: 이동유형 필터 (in/out/adjust)
            start_date: 시작일 필터
            end_date: 종료일 필터
            skip: offset
            limit: limit

        Returns:
            dict with movements list and summary (total_in, total_out, net_change)
        """
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if product_id is not None:
            where_clauses.append("m.product_id = :product_id")
            params["product_id"] = product_id

        if movement_type is not None:
            where_clauses.append("m.movement_type = :movement_type")
            params["movement_type"] = movement_type

        if start_date is not None:
            where_clauses.append("m.movement_date >= :start_date")
            params["start_date"] = start_date

        if end_date is not None:
            where_clauses.append("m.movement_date <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # 이동 내역 조회
        query = text(f"""
            SELECT
                m.id,
                m.movement_date,
                m.movement_type,
                m.product_id,
                p.code AS product_code,
                p.name AS product_name,
                m.quantity,
                COALESCE(m.unit_cost, 0) AS unit_cost,
                m.reason,
                COALESCE(m.before_qty, 0) AS before_qty,
                COALESCE(m.after_qty, 0) AS after_qty,
                m.created_at
            FROM erp_inventory_movements m
            LEFT JOIN erp_products p ON p.id = m.product_id
            WHERE {where_sql}
            ORDER BY m.movement_date DESC, m.created_at DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        movements = [self._row_to_dict(row) for row in rows]

        # summary 집계 (같은 필터 조건, skip/limit 없이)
        summary_query = text(f"""
            SELECT
                COALESCE(SUM(CASE WHEN m.movement_type = 'in' THEN m.quantity ELSE 0 END), 0) AS total_in,
                COALESCE(SUM(CASE WHEN m.movement_type = 'out' THEN m.quantity ELSE 0 END), 0) AS total_out
            FROM erp_inventory_movements m
            WHERE {where_sql}
        """)

        # summary params: skip/limit 제외
        summary_params = {k: v for k, v in params.items() if k not in ("skip", "limit")}
        summary_result = await session.execute(summary_query, summary_params)
        summary_row = summary_result.mappings().first()

        total_in = float(summary_row["total_in"]) if summary_row else 0
        total_out = float(summary_row["total_out"]) if summary_row else 0

        return {
            "movements": movements,
            "summary": {
                "total_in": total_in,
                "total_out": total_out,
                "net_change": total_in - total_out,
            },
        }
