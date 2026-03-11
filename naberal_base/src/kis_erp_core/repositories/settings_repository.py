"""
Settings Repository
환경설정 + 사업장 마감 CRUD (erp_settings + erp_business_periods)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SettingsRepository:
    """환경설정 리포지토리"""

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in ("id", "closed_by"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    # ==================== Settings (Single-Row JSONB) ====================

    async def get_settings(self, session: AsyncSession) -> dict:
        """
        환경설정 조회 (단일행 JSONB)

        Returns:
            dict with settings JSONB merged with updated_at
        """
        query = text("""
            SELECT id, settings, updated_at
            FROM erp_settings
            LIMIT 1
        """)
        result = await session.execute(query)
        row = result.mappings().first()

        if not row:
            return {
                "fiscal_year_start_month": 1,
                "tax_rate": 10.0,
                "currency": "KRW",
                "decimal_places": 0,
                "voucher_number_format": "{TYPE}-{YYYYMMDD}-{SEQ:04d}",
                "order_number_format": "PO-{YYYYMMDD}-{SEQ:04d}",
                "statement_number_format": "{TYPE}-{YYYYMMDD}-{SEQ:04d}",
                "cost_method": "moving_average",
                "allow_negative_stock": False,
                "low_stock_alert": True,
                "updated_at": None,
            }

        row_dict = self._row_to_dict(row)
        settings_data = row_dict.get("settings", {})
        settings_data["updated_at"] = row_dict.get("updated_at")
        return settings_data

    async def update_settings(self, session: AsyncSession, data: dict) -> dict:
        """
        환경설정 업데이트 (기존 JSONB에 병합)

        Args:
            session: AsyncSession
            data: 업데이트할 설정 key-value dict

        Returns:
            Updated settings dict
        """
        query = text("""
            UPDATE erp_settings
            SET
                settings = settings || :patch,
                updated_at = timezone('utc', now())
            RETURNING id, settings, updated_at
        """)

        result = await session.execute(query, {"patch": json.dumps(data)})
        row = result.mappings().first()

        if not row:
            raise RuntimeError("Failed to update settings: no settings row found")

        row_dict = self._row_to_dict(row)
        settings_data = row_dict.get("settings", {})
        settings_data["updated_at"] = row_dict.get("updated_at")
        return settings_data

    # ==================== User Preferences (Column Visibility etc.) ====================

    async def get_preferences(self, session: AsyncSession) -> dict:
        """
        UI 사용자 환경설정 조회 (표시항목 등)

        erp_settings JSONB 내 'column_preferences' 키에서 읽음.

        Returns:
            dict: {"customer": ["col1", ...], "product": ["col1", ...], ...}
        """
        query = text("""
            SELECT settings->'column_preferences' AS prefs
            FROM erp_settings
            LIMIT 1
        """)
        result = await session.execute(query)
        row = result.mappings().first()

        if not row or row["prefs"] is None:
            return {}

        prefs = row["prefs"]
        return prefs if isinstance(prefs, dict) else {}

    async def update_preferences(self, session: AsyncSession, data: dict) -> dict:
        """
        UI 사용자 환경설정 저장 (표시항목 등)

        기존 column_preferences에 병합 (||) 후 저장.
        예: {"customer": ["code","name"]} → column_preferences.customer 업데이트

        Args:
            session: AsyncSession
            data: 윈도우별 표시 컬럼 dict (예: {"customer": ["code","name","ceo"]})

        Returns:
            Updated preferences dict
        """
        query = text("""
            UPDATE erp_settings
            SET
                settings = jsonb_set(
                    COALESCE(settings, '{}'::jsonb),
                    '{column_preferences}',
                    COALESCE(settings->'column_preferences', '{}'::jsonb) || :prefs::jsonb,
                    true
                ),
                updated_at = timezone('utc', now())
            RETURNING settings->'column_preferences' AS prefs
        """)

        result = await session.execute(query, {"prefs": json.dumps(data)})
        row = result.mappings().first()

        if not row:
            raise RuntimeError("Failed to update preferences: no settings row found")

        prefs = row["prefs"]
        return prefs if isinstance(prefs, dict) else {}

    # ==================== Business Periods (Monthly Close) ====================

    async def list_periods(
        self, session: AsyncSession, year: int | None = None
    ) -> list[dict]:
        """
        사업장 마감현황 조회

        Args:
            session: AsyncSession
            year: 연도 필터 (None이면 전체)

        Returns:
            List of period dicts
        """
        if year is not None:
            query = text("""
                SELECT id, year, month, is_closed, closed_at, closed_by, notes,
                       created_at, updated_at
                FROM erp_business_periods
                WHERE year = :year
                ORDER BY year DESC, month DESC
            """)
            result = await session.execute(query, {"year": year})
        else:
            query = text("""
                SELECT id, year, month, is_closed, closed_at, closed_by, notes,
                       created_at, updated_at
                FROM erp_business_periods
                ORDER BY year DESC, month DESC
            """)
            result = await session.execute(query)

        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def close_period(
        self,
        session: AsyncSession,
        year: int,
        month: int,
        notes: str | None = None,
    ) -> dict:
        """
        월 마감 처리 (INSERT or UPDATE on conflict)

        Args:
            session: AsyncSession
            year: 연도
            month: 월
            notes: 비고

        Returns:
            Period dict (마감 완료)
        """
        query = text("""
            INSERT INTO erp_business_periods (year, month, is_closed, closed_at, notes, updated_at)
            VALUES (:year, :month, true, timezone('utc', now()), :notes, timezone('utc', now()))
            ON CONFLICT (year, month)
            DO UPDATE SET
                is_closed = true,
                closed_at = timezone('utc', now()),
                notes = :notes,
                updated_at = timezone('utc', now())
            RETURNING id, year, month, is_closed, closed_at, closed_by, notes,
                      created_at, updated_at
        """)

        result = await session.execute(query, {
            "year": year,
            "month": month,
            "notes": notes,
        })
        row = result.mappings().first()

        if not row:
            raise RuntimeError(f"Failed to close period {year}-{month}")

        return self._row_to_dict(row)

    async def reopen_period(
        self,
        session: AsyncSession,
        year: int,
        month: int,
        reason: str,
    ) -> dict | None:
        """
        월 마감해제

        Args:
            session: AsyncSession
            year: 연도
            month: 월
            reason: 마감해제 사유

        Returns:
            Updated period dict, or None if not found
        """
        query = text("""
            UPDATE erp_business_periods
            SET
                is_closed = false,
                closed_at = NULL,
                notes = :reason,
                updated_at = timezone('utc', now())
            WHERE year = :year AND month = :month
            RETURNING id, year, month, is_closed, closed_at, closed_by, notes,
                      created_at, updated_at
        """)

        result = await session.execute(query, {
            "year": year,
            "month": month,
            "reason": reason,
        })
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_dict(row)
