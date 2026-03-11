"""
Employee Repository
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.product_employee_models import EmployeeCreate, EmployeeUpdate, EmployeeFilter


class EmployeeRepository:
    """Employee 리포지토리"""

    async def create(self, session: AsyncSession, data: EmployeeCreate) -> dict:
        """사원 생성"""
        emp_no = await self.generate_emp_no(session)

        query = text("""
            INSERT INTO erp.employees (
                id, emp_no, name, department, position, tel, email, status,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :emp_no, :name, :department, :position,
                :tel, :email, 'active',
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, emp_no, name, department, position, tel, email, status,
                created_at, updated_at
        """)

        result = await session.execute(query, {
            "emp_no": emp_no,
            "name": data.name,
            "department": data.department,
            "position": data.position,
            "tel": data.tel,
            "email": data.email,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create employee")

        # UUID를 str로 변환
        data = dict(row)
        data["id"] = str(data["id"])
        return data

    async def get(self, session: AsyncSession, id: UUID) -> Optional[dict]:
        """사원 조회"""
        query = text("""
            SELECT
                id, emp_no, name, department, position, tel, email, status,
                created_at, updated_at
            FROM erp.employees
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
        filters: EmployeeFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """사원 목록 조회"""
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if filters.department:
            where_clauses.append("department = :department")
            params["department"] = filters.department

        if filters.status:
            where_clauses.append("status = :status")
            params["status"] = filters.status

        if filters.search:
            where_clauses.append("(name ILIKE :search OR emp_no ILIKE :search)")
            params["search"] = f"%{filters.search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                id, emp_no, name, department, position, tel, email, status,
                created_at, updated_at
            FROM erp.employees
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
        data: EmployeeUpdate
    ) -> Optional[dict]:
        """사원 수정"""
        updates = []
        params = {"id": str(id)}

        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name

        if data.department is not None:
            updates.append("department = :department")
            params["department"] = data.department

        if data.position is not None:
            updates.append("position = :position")
            params["position"] = data.position

        if data.tel is not None:
            updates.append("tel = :tel")
            params["tel"] = data.tel

        if data.email is not None:
            updates.append("email = :email")
            params["email"] = data.email

        if data.status is not None:
            updates.append("status = :status")
            params["status"] = data.status

        if not updates:
            return await self.get(session, id)

        updates.append("updated_at = timezone('utc', now())")
        update_sql = ", ".join(updates)

        query = text(f"""
            UPDATE erp.employees
            SET {update_sql}
            WHERE id = :id
            RETURNING
                id, emp_no, name, department, position, tel, email, status,
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
        """사원 삭제 (soft delete - status를 resigned로 변경)"""
        query = text("""
            UPDATE erp.employees
            SET status = 'resigned', updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING id
        """)

        result = await session.execute(query, {"id": str(id)})
        row = result.mappings().first()

        return row is not None

    async def generate_emp_no(self, session: AsyncSession) -> str:
        """사원번호 자동 생성"""
        query = text("""
            SELECT emp_no
            FROM erp.employees
            ORDER BY emp_no DESC
            LIMIT 1
        """)

        result = await session.execute(query)
        row = result.mappings().first()

        if not row:
            return "E0001"

        last_emp_no = row["emp_no"]
        number = int(last_emp_no[1:]) + 1
        return f"E{number:04d}"
