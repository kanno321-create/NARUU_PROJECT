"""
Customer Repository
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.erp_models import CustomerCreate, CustomerUpdate, CustomerFilter


class CustomerRepository:
    """
    Customer 리포지토리

    Dual-DSN 패턴:
    - Alembic: psycopg2 (마이그레이션)
    - App: asyncpg (런타임)
    """

    async def create(self, session: AsyncSession, data: CustomerCreate) -> dict:
        """
        거래처 생성

        Args:
            session: AsyncSession
            data: CustomerCreate

        Returns:
            Customer dict
        """
        # 거래처 코드 자동 생성
        code = await self.generate_code(session)

        query = text("""
            INSERT INTO erp.customers (
                id, code, name, type, business_number, ceo, contact,
                address, tel, fax, email, mobile, balance, credit_limit,
                payment_terms, bank_info, memo, is_active,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :code, :name, :type, :business_number,
                :ceo, :contact, :address, :tel, :fax, :email, :mobile,
                0, :credit_limit, :payment_terms, :bank_info, :memo, true,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, code, name, type, business_number, ceo, contact,
                address, tel, fax, email, mobile, balance, credit_limit,
                payment_terms, bank_info, memo, is_active,
                created_at, updated_at
        """)

        result = await session.execute(query, {
            "code": code,
            "name": data.name,
            "type": data.type,
            "business_number": data.business_number,
            "ceo": data.ceo,
            "contact": data.contact,
            "address": data.address,
            "tel": data.tel,
            "fax": data.fax,
            "email": data.email,
            "mobile": data.mobile,
            "credit_limit": data.credit_limit,
            "payment_terms": data.payment_terms,
            "bank_info": data.bank_info,
            "memo": data.memo,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create customer")

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def get(self, session: AsyncSession, id: UUID) -> Optional[dict]:
        """
        거래처 조회

        Args:
            session: AsyncSession
            id: Customer ID

        Returns:
            Customer dict or None
        """
        query = text("""
            SELECT
                id, code, name, type, business_number, ceo, contact,
                address, tel, fax, email, mobile, balance, credit_limit,
                payment_terms, bank_info, memo, is_active,
                created_at, updated_at
            FROM erp.customers
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
        filters: CustomerFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """
        거래처 목록 조회

        Args:
            session: AsyncSession
            filters: CustomerFilter
            skip: offset
            limit: limit

        Returns:
            List of Customer dicts
        """
        # Base query
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        # 필터 조건 추가
        if filters.type:
            where_clauses.append("type = :type")
            params["type"] = filters.type

        if filters.is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = filters.is_active

        if filters.search:
            where_clauses.append("(name ILIKE :search OR code ILIKE :search)")
            params["search"] = f"%{filters.search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                id, code, name, type, business_number, ceo, contact,
                address, tel, fax, email, mobile, balance, credit_limit,
                payment_terms, bank_info, memo, is_active,
                created_at, updated_at
            FROM erp.customers
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
        data: CustomerUpdate
    ) -> Optional[dict]:
        """
        거래처 수정

        Args:
            session: AsyncSession
            id: Customer ID
            data: CustomerUpdate

        Returns:
            Updated Customer dict or None
        """
        # 수정할 필드만 동적으로 추가
        updates = []
        params = {"id": str(id)}

        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name

        if data.type is not None:
            updates.append("type = :type")
            params["type"] = data.type

        if data.business_number is not None:
            updates.append("business_number = :business_number")
            params["business_number"] = data.business_number

        if data.ceo is not None:
            updates.append("ceo = :ceo")
            params["ceo"] = data.ceo

        if data.contact is not None:
            updates.append("contact = :contact")
            params["contact"] = data.contact

        if data.address is not None:
            updates.append("address = :address")
            params["address"] = data.address

        if data.tel is not None:
            updates.append("tel = :tel")
            params["tel"] = data.tel

        if data.fax is not None:
            updates.append("fax = :fax")
            params["fax"] = data.fax

        if data.email is not None:
            updates.append("email = :email")
            params["email"] = data.email

        if data.mobile is not None:
            updates.append("mobile = :mobile")
            params["mobile"] = data.mobile

        if data.credit_limit is not None:
            updates.append("credit_limit = :credit_limit")
            params["credit_limit"] = data.credit_limit

        if data.payment_terms is not None:
            updates.append("payment_terms = :payment_terms")
            params["payment_terms"] = data.payment_terms

        if data.bank_info is not None:
            updates.append("bank_info = :bank_info")
            params["bank_info"] = data.bank_info

        if data.memo is not None:
            updates.append("memo = :memo")
            params["memo"] = data.memo

        if data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if not updates:
            # 수정할 내용 없으면 조회만
            return await self.get(session, id)

        updates.append("updated_at = timezone('utc', now())")
        update_sql = ", ".join(updates)

        query = text(f"""
            UPDATE erp.customers
            SET {update_sql}
            WHERE id = :id
            RETURNING
                id, code, name, type, business_number, ceo, contact,
                address, tel, fax, email, mobile, balance, credit_limit,
                payment_terms, bank_info, memo, is_active,
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
        """
        거래처 삭제 (soft delete)

        Args:
            session: AsyncSession
            id: Customer ID

        Returns:
            Success boolean
        """
        query = text("""
            UPDATE erp.customers
            SET is_active = false, updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING id
        """)

        result = await session.execute(query, {"id": str(id)})
        row = result.mappings().first()

        return row is not None

    async def get_balance(self, session: AsyncSession, id: UUID) -> Decimal:
        """
        거래처 잔액 조회

        Args:
            session: AsyncSession
            id: Customer ID

        Returns:
            Balance (Decimal)
        """
        query = text("""
            SELECT balance
            FROM erp.customers
            WHERE id = :id
        """)

        result = await session.execute(query, {"id": str(id)})
        row = result.mappings().first()

        if not row:
            return Decimal("0.00")

        return Decimal(str(row["balance"]))

    async def generate_code(self, session: AsyncSession) -> str:
        """
        거래처 코드 자동 생성

        Args:
            session: AsyncSession

        Returns:
            Generated customer code (e.g., "C0001")
        """
        query = text("""
            SELECT code
            FROM erp.customers
            ORDER BY code DESC
            LIMIT 1
        """)

        result = await session.execute(query)
        row = result.mappings().first()

        if not row:
            return "C0001"

        last_code = row["code"]
        # "C0001" -> 1 -> 2 -> "C0002"
        number = int(last_code[1:]) + 1
        return f"C{number:04d}"
