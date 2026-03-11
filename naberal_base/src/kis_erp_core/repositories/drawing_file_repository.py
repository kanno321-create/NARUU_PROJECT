"""
DrawingFile Repository
도면 파일 BYTEA 저장소
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DrawingFileRepository:
    """도면 파일 리포지토리 — Railway PostgreSQL BYTEA 저장"""

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS erp_drawing_files (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        drawing_name TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_data BYTEA NOT NULL,
        file_size BIGINT NOT NULL,
        project_name TEXT,
        customer_name TEXT,
        description TEXT,
        tags TEXT[] DEFAULT '{}',
        version INT DEFAULT 1,
        status TEXT DEFAULT 'uploaded',
        created_at TIMESTAMPTZ DEFAULT timezone('utc', now()),
        updated_at TIMESTAMPTZ DEFAULT timezone('utc', now())
    )
    """

    async def ensure_table(self, session: AsyncSession) -> None:
        """테이블이 없으면 생성"""
        await session.execute(text(self.TABLE_DDL))
        await session.commit()

    async def save(
        self,
        session: AsyncSession,
        drawing_name: str,
        file_name: str,
        file_type: str,
        file_data: bytes,
        project_name: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> dict:
        """도면 파일 저장"""
        query = text("""
            INSERT INTO erp_drawing_files (
                id, drawing_name, file_name, file_type, file_data, file_size,
                project_name, customer_name, description, tags,
                version, status, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :drawing_name, :file_name, :file_type, :file_data,
                :file_size, :project_name, :customer_name, :description, :tags,
                1, 'uploaded', timezone('utc', now()), timezone('utc', now())
            )
            RETURNING id, drawing_name, file_name, file_type, file_size,
                      project_name, customer_name, description, tags,
                      version, status, created_at, updated_at
        """)

        result = await session.execute(query, {
            "drawing_name": drawing_name,
            "file_name": file_name,
            "file_type": file_type,
            "file_data": file_data,
            "file_size": len(file_data),
            "project_name": project_name,
            "customer_name": customer_name,
            "description": description,
            "tags": tags or [],
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to save drawing file")

        row_dict = dict(row)
        row_dict["id"] = str(row_dict["id"])
        row_dict["tags"] = list(row_dict["tags"]) if row_dict["tags"] else []
        return row_dict

    async def get(self, session: AsyncSession, file_id: str) -> Optional[dict]:
        """파일 메타데이터 조회 (file_data 제외)"""
        query = text("""
            SELECT id, drawing_name, file_name, file_type, file_size,
                   project_name, customer_name, description, tags,
                   version, status, created_at, updated_at
            FROM erp_drawing_files
            WHERE id = :id
        """)
        result = await session.execute(query, {"id": file_id})
        row = result.mappings().first()
        if not row:
            return None
        row_dict = dict(row)
        row_dict["id"] = str(row_dict["id"])
        row_dict["tags"] = list(row_dict["tags"]) if row_dict["tags"] else []
        return row_dict

    async def get_file_data(self, session: AsyncSession, file_id: str) -> Optional[dict]:
        """파일 데이터 포함 조회"""
        query = text("""
            SELECT id, drawing_name, file_name, file_type, file_data, file_size,
                   project_name, customer_name, description, tags,
                   version, status, created_at, updated_at
            FROM erp_drawing_files
            WHERE id = :id
        """)
        result = await session.execute(query, {"id": file_id})
        row = result.mappings().first()
        if not row:
            return None
        row_dict = dict(row)
        row_dict["id"] = str(row_dict["id"])
        row_dict["tags"] = list(row_dict["tags"]) if row_dict["tags"] else []
        return row_dict

    async def list(
        self,
        session: AsyncSession,
        search: Optional[str] = None,
        project_name: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """도면 파일 목록 (file_data 제외)"""
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if search:
            where_clauses.append(
                "(drawing_name ILIKE :search OR file_name ILIKE :search OR customer_name ILIKE :search)"
            )
            params["search"] = f"%{search}%"

        if project_name:
            where_clauses.append("project_name = :project_name")
            params["project_name"] = project_name

        if status:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT id, drawing_name, file_name, file_type, file_size,
                   project_name, customer_name, description, tags,
                   version, status, created_at, updated_at
            FROM erp_drawing_files
            WHERE {where_sql}
            ORDER BY created_at DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [
            {
                **dict(row),
                "id": str(row["id"]),
                "tags": list(row["tags"]) if row["tags"] else [],
            }
            for row in rows
        ]

    async def update(
        self, session: AsyncSession, file_id: str, data: dict
    ) -> Optional[dict]:
        """도면 메타데이터 수정"""
        updates = []
        params: dict = {"id": file_id}

        for field in ("drawing_name", "project_name", "customer_name", "description", "status"):
            if field in data and data[field] is not None:
                updates.append(f"{field} = :{field}")
                params[field] = data[field]

        if "tags" in data:
            updates.append("tags = :tags")
            params["tags"] = data["tags"] or []

        if not updates:
            return await self.get(session, file_id)

        updates.append("updated_at = timezone('utc', now())")
        update_sql = ", ".join(updates)

        query = text(f"""
            UPDATE erp_drawing_files
            SET {update_sql}
            WHERE id = :id
            RETURNING id, drawing_name, file_name, file_type, file_size,
                      project_name, customer_name, description, tags,
                      version, status, created_at, updated_at
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()
        if not row:
            return None
        row_dict = dict(row)
        row_dict["id"] = str(row_dict["id"])
        row_dict["tags"] = list(row_dict["tags"]) if row_dict["tags"] else []
        return row_dict

    async def delete(self, session: AsyncSession, file_id: str) -> bool:
        """도면 파일 삭제"""
        query = text("""
            DELETE FROM erp_drawing_files WHERE id = :id RETURNING id
        """)
        result = await session.execute(query, {"id": file_id})
        row = result.mappings().first()
        return row is not None
