"""
EstimateFile Repository
견적 파일(Excel/PDF) BYTEA 저장소
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class EstimateFileRepository:
    """견적 파일 리포지토리 — Railway PostgreSQL BYTEA 저장"""

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS erp_estimate_files (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        estimate_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL CHECK (file_type IN ('xlsx', 'pdf')),
        file_data BYTEA NOT NULL,
        file_size BIGINT NOT NULL,
        customer_name TEXT,
        total_price NUMERIC(15, 2),
        created_at TIMESTAMPTZ DEFAULT timezone('utc', now())
    )
    """

    async def ensure_table(self, session: AsyncSession) -> None:
        """테이블이 없으면 생성"""
        await session.execute(text(self.TABLE_DDL))
        await session.commit()

    async def save(
        self,
        session: AsyncSession,
        estimate_id: str,
        file_name: str,
        file_type: str,
        file_data: bytes,
        customer_name: Optional[str] = None,
        total_price: Optional[float] = None,
    ) -> dict:
        """견적 파일 저장"""
        query = text("""
            INSERT INTO erp_estimate_files (
                id, estimate_id, file_name, file_type, file_data, file_size,
                customer_name, total_price, created_at
            ) VALUES (
                gen_random_uuid(), :estimate_id, :file_name, :file_type, :file_data,
                :file_size, :customer_name, :total_price, timezone('utc', now())
            )
            RETURNING id, estimate_id, file_name, file_type, file_size,
                      customer_name, total_price, created_at
        """)

        result = await session.execute(query, {
            "estimate_id": estimate_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_data": file_data,
            "file_size": len(file_data),
            "customer_name": customer_name,
            "total_price": total_price,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to save estimate file")

        return {**dict(row), "id": str(row["id"])}

    async def get(self, session: AsyncSession, file_id: str) -> Optional[dict]:
        """파일 메타데이터 조회 (file_data 제외)"""
        query = text("""
            SELECT id, estimate_id, file_name, file_type, file_size,
                   customer_name, total_price, created_at
            FROM erp_estimate_files
            WHERE id = :id
        """)
        result = await session.execute(query, {"id": file_id})
        row = result.mappings().first()
        if not row:
            return None
        return {**dict(row), "id": str(row["id"])}

    async def get_file_data(self, session: AsyncSession, file_id: str) -> Optional[dict]:
        """파일 데이터 포함 조회"""
        query = text("""
            SELECT id, estimate_id, file_name, file_type, file_data, file_size,
                   customer_name, total_price, created_at
            FROM erp_estimate_files
            WHERE id = :id
        """)
        result = await session.execute(query, {"id": file_id})
        row = result.mappings().first()
        if not row:
            return None
        return {**dict(row), "id": str(row["id"])}

    async def list(
        self,
        session: AsyncSession,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """견적 파일 목록 (file_data 제외)"""
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if search:
            where_clauses.append(
                "(estimate_id ILIKE :search OR file_name ILIKE :search OR customer_name ILIKE :search)"
            )
            params["search"] = f"%{search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT id, estimate_id, file_name, file_type, file_size,
                   customer_name, total_price, created_at
            FROM erp_estimate_files
            WHERE {where_sql}
            ORDER BY created_at DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [{**dict(row), "id": str(row["id"])} for row in rows]

    async def delete(self, session: AsyncSession, file_id: str) -> bool:
        """견적 파일 삭제"""
        query = text("""
            DELETE FROM erp_estimate_files WHERE id = :id RETURNING id
        """)
        result = await session.execute(query, {"id": file_id})
        row = result.mappings().first()
        return row is not None
