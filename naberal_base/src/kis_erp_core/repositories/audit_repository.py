"""
Audit Repository
감사추적 로그 CRUD (erp_audit_log)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AuditRepository:
    """감사추적 리포지토리"""

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in ("id",):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    async def log_change(
        self,
        session: AsyncSession,
        table_name: str,
        record_id: str,
        action: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        changed_by: str | None = None,
        ip_address: str | None = None,
        description: str | None = None,
    ) -> dict:
        """
        변경 이력 기록

        Args:
            session: AsyncSession
            table_name: 변경 테이블명
            record_id: 변경 레코드 ID
            action: INSERT/UPDATE/DELETE
            old_values: 변경 전 값 (dict)
            new_values: 변경 후 값 (dict)
            changed_by: 변경자
            ip_address: IP 주소
            description: 변경 설명

        Returns:
            생성된 audit log dict
        """
        query = text("""
            INSERT INTO erp_audit_log
                (table_name, record_id, action, changed_by, old_values, new_values, ip_address, description)
            VALUES
                (:table_name, :record_id, :action, :changed_by, :old_values, :new_values, :ip_address, :description)
            RETURNING id, table_name, record_id, action, changed_by, changed_at,
                      old_values, new_values, ip_address, description
        """)

        result = await session.execute(query, {
            "table_name": table_name,
            "record_id": record_id,
            "action": action,
            "changed_by": changed_by,
            "old_values": json.dumps(old_values) if old_values is not None else None,
            "new_values": json.dumps(new_values) if new_values is not None else None,
            "ip_address": ip_address,
            "description": description,
        })
        row = result.mappings().first()

        if not row:
            raise RuntimeError("Failed to insert audit log")

        return self._row_to_dict(row)

    async def list_logs(
        self,
        session: AsyncSession,
        table_name: str | None = None,
        record_id: str | None = None,
        action: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        """
        감사 로그 목록 조회 (필터 지원)

        Args:
            session: AsyncSession
            table_name: 테이블명 필터
            record_id: 레코드 ID 필터
            action: 액션 필터 (INSERT/UPDATE/DELETE)
            start_date: 시작일 (ISO 8601)
            end_date: 종료일 (ISO 8601)
            skip: 건너뛸 행 수
            limit: 최대 반환 행 수

        Returns:
            List of audit log dicts
        """
        conditions = []
        params: dict = {"skip": skip, "limit": limit}

        if table_name is not None:
            conditions.append("table_name = :table_name")
            params["table_name"] = table_name

        if record_id is not None:
            conditions.append("record_id = :record_id")
            params["record_id"] = record_id

        if action is not None:
            conditions.append("action = :action")
            params["action"] = action

        if start_date is not None:
            conditions.append("changed_at >= :start_date::timestamptz")
            params["start_date"] = start_date

        if end_date is not None:
            conditions.append("changed_at <= :end_date::timestamptz")
            params["end_date"] = end_date

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = text(f"""
            SELECT id, table_name, record_id, action, changed_by, changed_at,
                   old_values, new_values, ip_address, description
            FROM erp_audit_log
            {where_clause}
            ORDER BY changed_at DESC
            OFFSET :skip LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def get_record_history(
        self,
        session: AsyncSession,
        table_name: str,
        record_id: str,
    ) -> list[dict]:
        """
        특정 레코드의 전체 변경 이력 조회

        Args:
            session: AsyncSession
            table_name: 테이블명
            record_id: 레코드 ID

        Returns:
            해당 레코드의 변경 이력 리스트 (최신순)
        """
        query = text("""
            SELECT id, table_name, record_id, action, changed_by, changed_at,
                   old_values, new_values, ip_address, description
            FROM erp_audit_log
            WHERE table_name = :table_name AND record_id = :record_id
            ORDER BY changed_at DESC
        """)

        result = await session.execute(query, {
            "table_name": table_name,
            "record_id": record_id,
        })
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]
