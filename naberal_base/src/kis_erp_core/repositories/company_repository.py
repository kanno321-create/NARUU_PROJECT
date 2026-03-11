"""
Company Repository
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.erp_models import CompanyCreate, CompanyUpdate


class CompanyRepository:
    """
    Company 리포지토리

    Note: 자사정보는 1개만 존재
    """

    async def get(self, session: AsyncSession) -> Optional[dict]:
        """
        자사정보 조회

        Returns:
            Company dict or None
        """
        query = text("""
            SELECT
                id, business_number, name, ceo, address, tel, fax, email,
                bank_info, business_type, business_item, logo_path,
                stamp_path, created_at, updated_at
            FROM erp.company
            LIMIT 1
        """)

        result = await session.execute(query)
        row = result.mappings().first()

        if not row:
            return None

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def create(self, session: AsyncSession, data: CompanyCreate) -> dict:
        """
        자사정보 생성

        Note: 이미 존재하면 에러
        """
        # 기존 데이터 확인
        existing = await self.get(session)
        if existing:
            raise ValueError("Company info already exists")

        query = text("""
            INSERT INTO erp.company (
                id, business_number, name, ceo, address, tel, fax, email,
                bank_info, business_type, business_item, logo_path, stamp_path,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :business_number, :name, :ceo, :address,
                :tel, :fax, :email, :bank_info, :business_type, :business_item,
                :logo_path, :stamp_path,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, business_number, name, ceo, address, tel, fax, email,
                bank_info, business_type, business_item, logo_path,
                stamp_path, created_at, updated_at
        """)

        result = await session.execute(query, {
            "business_number": data.business_number,
            "name": data.name,
            "ceo": data.ceo,
            "address": data.address,
            "tel": data.tel,
            "fax": data.fax,
            "email": data.email,
            "bank_info": data.bank_info,
            "business_type": data.business_type,
            "business_item": data.business_item,
            "logo_path": data.logo_path,
            "stamp_path": data.stamp_path,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create company")

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def update(self, session: AsyncSession, data: CompanyUpdate) -> Optional[dict]:
        """
        자사정보 수정

        Note: 첫 번째(유일한) 레코드 수정
        """
        updates = []
        params = {}

        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name

        if data.ceo is not None:
            updates.append("ceo = :ceo")
            params["ceo"] = data.ceo

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

        if data.bank_info is not None:
            updates.append("bank_info = :bank_info")
            params["bank_info"] = data.bank_info

        if data.business_type is not None:
            updates.append("business_type = :business_type")
            params["business_type"] = data.business_type

        if data.business_item is not None:
            updates.append("business_item = :business_item")
            params["business_item"] = data.business_item

        if data.logo_path is not None:
            updates.append("logo_path = :logo_path")
            params["logo_path"] = data.logo_path

        if data.stamp_path is not None:
            updates.append("stamp_path = :stamp_path")
            params["stamp_path"] = data.stamp_path

        if not updates:
            return await self.get(session)

        updates.append("updated_at = timezone('utc', now())")
        update_sql = ", ".join(updates)

        query = text(f"""
            UPDATE erp.company
            SET {update_sql}
            RETURNING
                id, business_number, name, ceo, address, tel, fax, email,
                bank_info, business_type, business_item, logo_path,
                stamp_path, created_at, updated_at
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data
