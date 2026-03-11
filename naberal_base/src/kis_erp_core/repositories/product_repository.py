"""
Product Repository
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.product_employee_models import ProductCreate, ProductUpdate, ProductFilter


class ProductRepository:
    """Product 리포지토리"""

    async def create(self, session: AsyncSession, data: ProductCreate) -> dict:
        """상품 생성"""
        code = await self.generate_code(session)

        query = text("""
            INSERT INTO erp.products (
                id, code, name, category, unit, unit_cost, sale_price,
                stock_qty, spec, manufacturer, is_active,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :code, :name, :category, :unit,
                :unit_cost, :sale_price, 0, :spec, :manufacturer, true,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, code, name, category, unit, unit_cost, sale_price,
                stock_qty, spec, manufacturer, is_active,
                created_at, updated_at
        """)

        result = await session.execute(query, {
            "code": code,
            "name": data.name,
            "category": data.category,
            "unit": data.unit,
            "unit_cost": data.unit_cost,
            "sale_price": data.sale_price,
            "spec": data.spec,
            "manufacturer": data.manufacturer,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create product")

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def get(self, session: AsyncSession, id: UUID) -> Optional[dict]:
        """상품 조회"""
        query = text("""
            SELECT
                id, code, name, category, unit, unit_cost, sale_price,
                stock_qty, spec, manufacturer, is_active,
                created_at, updated_at
            FROM erp.products
            WHERE id = :id
        """)

        result = await session.execute(query, {"id": str(id)})
        row = result.mappings().first()

        if not row:
            return None

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def list(
        self,
        session: AsyncSession,
        filters: ProductFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """상품 목록 조회"""
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if filters.category:
            where_clauses.append("category = :category")
            params["category"] = filters.category

        if filters.is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = filters.is_active

        if filters.search:
            where_clauses.append("(name ILIKE :search OR code ILIKE :search)")
            params["search"] = f"%{filters.search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                id, code, name, category, unit, unit_cost, sale_price,
                stock_qty, spec, manufacturer, is_active,
                created_at, updated_at
            FROM erp.products
            WHERE {where_sql}
            ORDER BY created_at DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()

        # UUID를 str로 변환
        return [{**dict(row), "id": str(row["id"])} for row in rows]

    async def update(
        self,
        session: AsyncSession,
        id: UUID,
        data: ProductUpdate
    ) -> Optional[dict]:
        """상품 수정"""
        updates = []
        params = {"id": str(id)}

        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name

        if data.category is not None:
            updates.append("category = :category")
            params["category"] = data.category

        if data.unit is not None:
            updates.append("unit = :unit")
            params["unit"] = data.unit

        if data.unit_cost is not None:
            updates.append("unit_cost = :unit_cost")
            params["unit_cost"] = data.unit_cost

        if data.sale_price is not None:
            updates.append("sale_price = :sale_price")
            params["sale_price"] = data.sale_price

        if data.spec is not None:
            updates.append("spec = :spec")
            params["spec"] = data.spec

        if data.manufacturer is not None:
            updates.append("manufacturer = :manufacturer")
            params["manufacturer"] = data.manufacturer

        if data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if not updates:
            return await self.get(session, id)

        updates.append("updated_at = timezone('utc', now())")
        update_sql = ", ".join(updates)

        query = text(f"""
            UPDATE erp.products
            SET {update_sql}
            WHERE id = :id
            RETURNING
                id, code, name, category, unit, unit_cost, sale_price,
                stock_qty, spec, manufacturer, is_active,
                created_at, updated_at
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def delete(self, session: AsyncSession, id: UUID) -> bool:
        """상품 삭제 (soft delete)"""
        query = text("""
            UPDATE erp.products
            SET is_active = false, updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING id
        """)

        result = await session.execute(query, {"id": str(id)})
        row = result.mappings().first()

        return row is not None

    async def adjust_stock(
        self,
        session: AsyncSession,
        id: UUID,
        qty: Decimal,
        reason: str
    ) -> Optional[dict]:
        """재고 조정"""
        query = text("""
            UPDATE erp.products
            SET
                stock_qty = stock_qty + :qty,
                updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING
                id, code, name, category, unit, unit_cost, sale_price,
                stock_qty, spec, manufacturer, is_active,
                created_at, updated_at
        """)

        result = await session.execute(query, {
            "id": str(id),
            "qty": float(qty)
        })
        row = result.mappings().first()

        if not row:
            return None

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def generate_code(self, session: AsyncSession) -> str:
        """상품 코드 자동 생성"""
        query = text("""
            SELECT code
            FROM erp.products
            ORDER BY code DESC
            LIMIT 1
        """)

        result = await session.execute(query)
        row = result.mappings().first()

        if not row:
            return "P0001"

        last_code = row["code"]
        number = int(last_code[1:]) + 1
        return f"P{number:04d}"
