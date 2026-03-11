"""
Payroll Repository
급여대장 CRUD (erp_payrolls + erp_payroll_items)
Contract-First + Evidence-Gated + Zero-Mock
"""

import json
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class PayrollRepository:
    """급여대장 리포지토리"""

    async def ensure_table(self, session: AsyncSession) -> None:
        """erp_payrolls / erp_payroll_items 테이블 생성 (IF NOT EXISTS)"""
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS erp_payrolls (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                year INT NOT NULL,
                month INT NOT NULL,
                pay_date DATE NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'draft',
                total_earnings NUMERIC(15,0) NOT NULL DEFAULT 0,
                total_deductions NUMERIC(15,0) NOT NULL DEFAULT 0,
                total_net_pay NUMERIC(15,0) NOT NULL DEFAULT 0,
                insurance_rates JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
                UNIQUE(year, month)
            )
        """))

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS erp_payroll_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                payroll_id UUID NOT NULL REFERENCES erp_payrolls(id) ON DELETE CASCADE,
                employee_id VARCHAR(100) NOT NULL,
                employee_name VARCHAR(100) NOT NULL,
                department VARCHAR(100),
                position VARCHAR(100),
                base_salary NUMERIC(15,0) NOT NULL DEFAULT 0,
                position_pay NUMERIC(15,0) NOT NULL DEFAULT 0,
                overtime_pay NUMERIC(15,0) NOT NULL DEFAULT 0,
                night_pay NUMERIC(15,0) NOT NULL DEFAULT 0,
                holiday_pay NUMERIC(15,0) NOT NULL DEFAULT 0,
                bonus NUMERIC(15,0) NOT NULL DEFAULT 0,
                allowances NUMERIC(15,0) NOT NULL DEFAULT 0,
                other_pay NUMERIC(15,0) NOT NULL DEFAULT 0,
                total_earnings NUMERIC(15,0) NOT NULL DEFAULT 0,
                income_tax NUMERIC(15,0) NOT NULL DEFAULT 0,
                local_income_tax NUMERIC(15,0) NOT NULL DEFAULT 0,
                national_pension NUMERIC(15,0) NOT NULL DEFAULT 0,
                health_insurance NUMERIC(15,0) NOT NULL DEFAULT 0,
                employment_insurance NUMERIC(15,0) NOT NULL DEFAULT 0,
                long_term_care NUMERIC(15,0) NOT NULL DEFAULT 0,
                other_deductions NUMERIC(15,0) NOT NULL DEFAULT 0,
                total_deductions NUMERIC(15,0) NOT NULL DEFAULT 0,
                net_pay NUMERIC(15,0) NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
            )
        """))

    def _row_to_dict(self, row) -> dict:
        """Row -> dict, UUID를 str로 변환"""
        data = dict(row)
        for key in ("id", "payroll_id"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    async def save(self, session: AsyncSession, payroll_data: dict) -> dict:
        """
        급여대장 저장 (INSERT).
        payroll_data = {year, month, pay_date, status, items: [...], insurance_rates: {...},
                        total_earnings, total_deductions, total_net_pay}
        """
        await self.ensure_table(session)

        query = text("""
            INSERT INTO erp_payrolls (
                year, month, pay_date, status,
                total_earnings, total_deductions, total_net_pay,
                insurance_rates,
                created_at, updated_at
            ) VALUES (
                :year, :month, :pay_date, :status,
                :total_earnings, :total_deductions, :total_net_pay,
                :insurance_rates::jsonb,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING id, year, month, pay_date, status,
                      total_earnings, total_deductions, total_net_pay,
                      insurance_rates, created_at, updated_at
        """)

        try:
            result = await session.execute(query, {
                "year": payroll_data["year"],
                "month": payroll_data["month"],
                "pay_date": payroll_data["pay_date"],
                "status": payroll_data.get("status", "draft"),
                "total_earnings": payroll_data.get("total_earnings", 0),
                "total_deductions": payroll_data.get("total_deductions", 0),
                "total_net_pay": payroll_data.get("total_net_pay", 0),
                "insurance_rates": json.dumps(payroll_data.get("insurance_rates", {})),
            })
        except IntegrityError:
            await session.rollback()
            raise RuntimeError("해당 연월의 급여대장이 이미 존재합니다")

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create payroll")

        payroll = self._row_to_dict(row)
        payroll_id = payroll["id"]

        # Insert items
        items = payroll_data.get("items", [])
        saved_items = []
        for item in items:
            saved_item = await self._insert_item(session, payroll_id, item)
            saved_items.append(saved_item)

        payroll["items"] = saved_items
        await session.commit()
        return payroll

    async def _insert_item(self, session: AsyncSession, payroll_id: str, item: dict) -> dict:
        """급여 항목 INSERT"""
        query = text("""
            INSERT INTO erp_payroll_items (
                payroll_id, employee_id, employee_name, department, position,
                base_salary, position_pay, overtime_pay, night_pay, holiday_pay,
                bonus, allowances, other_pay, total_earnings,
                income_tax, local_income_tax, national_pension,
                health_insurance, employment_insurance, long_term_care,
                other_deductions, total_deductions, net_pay, notes
            ) VALUES (
                :payroll_id::uuid, :employee_id, :employee_name, :department, :position,
                :base_salary, :position_pay, :overtime_pay, :night_pay, :holiday_pay,
                :bonus, :allowances, :other_pay, :total_earnings,
                :income_tax, :local_income_tax, :national_pension,
                :health_insurance, :employment_insurance, :long_term_care,
                :other_deductions, :total_deductions, :net_pay, :notes
            )
            RETURNING *
        """)

        result = await session.execute(query, {
            "payroll_id": payroll_id,
            "employee_id": item.get("employee_id", ""),
            "employee_name": item.get("employee_name", ""),
            "department": item.get("department"),
            "position": item.get("position"),
            "base_salary": item.get("base_salary", 0),
            "position_pay": item.get("position_pay", 0),
            "overtime_pay": item.get("overtime_pay", 0),
            "night_pay": item.get("night_pay", 0),
            "holiday_pay": item.get("holiday_pay", 0),
            "bonus": item.get("bonus", 0),
            "allowances": item.get("allowances", 0),
            "other_pay": item.get("other_pay", 0),
            "total_earnings": item.get("total_earnings", 0),
            "income_tax": item.get("income_tax", 0),
            "local_income_tax": item.get("local_income_tax", 0),
            "national_pension": item.get("national_pension", 0),
            "health_insurance": item.get("health_insurance", 0),
            "employment_insurance": item.get("employment_insurance", 0),
            "long_term_care": item.get("long_term_care", 0),
            "other_deductions": item.get("other_deductions", 0),
            "total_deductions": item.get("total_deductions", 0),
            "net_pay": item.get("net_pay", 0),
            "notes": item.get("notes"),
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to insert payroll item")
        return self._row_to_dict(row)

    async def get(self, session: AsyncSession, payroll_id: str) -> Optional[dict]:
        """급여대장 상세 조회 (items 포함)"""
        await self.ensure_table(session)

        query = text("""
            SELECT id, year, month, pay_date, status,
                   total_earnings, total_deductions, total_net_pay,
                   insurance_rates, created_at, updated_at
            FROM erp_payrolls
            WHERE id = :id
        """)
        result = await session.execute(query, {"id": payroll_id})
        row = result.mappings().first()
        if not row:
            return None

        payroll = self._row_to_dict(row)
        payroll["items"] = await self._get_items(session, payroll_id)
        return payroll

    async def get_by_period(self, session: AsyncSession, year: int, month: int) -> Optional[dict]:
        """특정 연월 급여대장 조회"""
        await self.ensure_table(session)

        query = text("""
            SELECT id, year, month, pay_date, status,
                   total_earnings, total_deductions, total_net_pay,
                   insurance_rates, created_at, updated_at
            FROM erp_payrolls
            WHERE year = :year AND month = :month
        """)
        result = await session.execute(query, {"year": year, "month": month})
        row = result.mappings().first()
        if not row:
            return None

        payroll = self._row_to_dict(row)
        payroll["items"] = await self._get_items(session, payroll["id"])
        return payroll

    async def _get_items(self, session: AsyncSession, payroll_id: str) -> List[dict]:
        """급여 항목 목록 조회"""
        query = text("""
            SELECT *
            FROM erp_payroll_items
            WHERE payroll_id = :payroll_id
            ORDER BY employee_name
        """)
        result = await session.execute(query, {"payroll_id": payroll_id})
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def list_by_period(
        self,
        session: AsyncSession,
        year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 12,
    ) -> List[dict]:
        """급여대장 목록 조회 (items 미포함)"""
        await self.ensure_table(session)

        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if year is not None:
            where_clauses.append("year = :year")
            params["year"] = year

        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT id, year, month, pay_date, status,
                   total_earnings, total_deductions, total_net_pay,
                   insurance_rates, created_at, updated_at
            FROM erp_payrolls
            WHERE {where_sql}
            ORDER BY year DESC, month DESC
            OFFSET :skip LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        payrolls = []
        for row in rows:
            p = self._row_to_dict(row)
            p["items"] = await self._get_items(session, p["id"])
            payrolls.append(p)
        return payrolls

    async def update(self, session: AsyncSession, payroll_id: str, data: dict) -> Optional[dict]:
        """급여대장 수정 (items 재작성)"""
        await self.ensure_table(session)

        # 기존 확인
        existing = await self.get(session, payroll_id)
        if not existing:
            return None

        if existing["status"] != "draft":
            raise RuntimeError("확정된 급여대장은 수정할 수 없습니다")

        # payroll 헤더 업데이트
        query = text("""
            UPDATE erp_payrolls
            SET pay_date = :pay_date,
                total_earnings = :total_earnings,
                total_deductions = :total_deductions,
                total_net_pay = :total_net_pay,
                insurance_rates = :insurance_rates::jsonb,
                updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING id, year, month, pay_date, status,
                      total_earnings, total_deductions, total_net_pay,
                      insurance_rates, created_at, updated_at
        """)

        result = await session.execute(query, {
            "id": payroll_id,
            "pay_date": data.get("pay_date", existing["pay_date"]),
            "total_earnings": data.get("total_earnings", 0),
            "total_deductions": data.get("total_deductions", 0),
            "total_net_pay": data.get("total_net_pay", 0),
            "insurance_rates": json.dumps(data.get("insurance_rates", {})),
        })

        row = result.mappings().first()
        if not row:
            return None

        payroll = self._row_to_dict(row)

        # 기존 items 삭제 후 재입력
        await session.execute(
            text("DELETE FROM erp_payroll_items WHERE payroll_id = :pid"),
            {"pid": payroll_id}
        )

        saved_items = []
        for item in data.get("items", []):
            saved_item = await self._insert_item(session, payroll_id, item)
            saved_items.append(saved_item)

        payroll["items"] = saved_items
        await session.commit()
        return payroll

    async def delete(self, session: AsyncSession, payroll_id: str) -> bool:
        """급여대장 삭제 (draft 상태만)"""
        await self.ensure_table(session)

        existing = await self.get(session, payroll_id)
        if not existing:
            return False

        if existing["status"] != "draft":
            raise RuntimeError("확정된 급여대장은 삭제할 수 없습니다")

        # CASCADE로 items도 삭제됨
        result = await session.execute(
            text("DELETE FROM erp_payrolls WHERE id = :id RETURNING id"),
            {"id": payroll_id}
        )
        deleted = result.mappings().first()
        await session.commit()
        return deleted is not None

    async def confirm(self, session: AsyncSession, payroll_id: str) -> Optional[dict]:
        """급여대장 확정"""
        await self.ensure_table(session)

        query = text("""
            UPDATE erp_payrolls
            SET status = 'confirmed', updated_at = timezone('utc', now())
            WHERE id = :id AND status = 'draft'
            RETURNING id, year, month, pay_date, status,
                      total_earnings, total_deductions, total_net_pay,
                      insurance_rates, created_at, updated_at
        """)
        result = await session.execute(query, {"id": payroll_id})
        row = result.mappings().first()
        if not row:
            return None

        payroll = self._row_to_dict(row)
        payroll["items"] = await self._get_items(session, payroll_id)
        await session.commit()
        return payroll

    async def pay(self, session: AsyncSession, payroll_id: str) -> Optional[dict]:
        """급여 지급 처리"""
        await self.ensure_table(session)

        query = text("""
            UPDATE erp_payrolls
            SET status = 'paid', updated_at = timezone('utc', now())
            WHERE id = :id AND status = 'confirmed'
            RETURNING id, year, month, pay_date, status,
                      total_earnings, total_deductions, total_net_pay,
                      insurance_rates, created_at, updated_at
        """)
        result = await session.execute(query, {"id": payroll_id})
        row = result.mappings().first()
        if not row:
            return None

        payroll = self._row_to_dict(row)
        payroll["items"] = await self._get_items(session, payroll_id)
        await session.commit()
        return payroll
