"""
Voucher Service
전표 비즈니스 로직 + 자동 분개(Auto Journal) 생성
Contract-First + Evidence-Gated + Zero-Mock

전표 유형별 자동 분개 규칙:
- sales(매출):    DR 매출채권(1100) + DR 부가세대급금(1400) / CR 상품매출(4100) + CR 부가세예수금(2400)
- purchase(매입): DR 상품매입(5100) + DR 부가세대급금(1400) / CR 매입채무(2100)
- receipt(수금):  DR 현금(1010) 또는 보통예금(1020) / CR 매출채권(1100)
- payment(지급):  DR 매입채무(2100) / CR 현금(1010) 또는 보통예금(1020)
- expense(지출):  DR 경비 계정 / CR 현금(1010) 또는 보통예금(1020)
"""
from datetime import date
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.voucher_models import (
    VoucherCreate,
    VoucherUpdate,
    VoucherFilter,
)
from kis_erp_core.repositories.voucher_repository import VoucherRepository
from kis_erp_core.repositories.account_repository import AccountRepository
from kis_erp_core.repositories.journal_repository import JournalRepository


class VoucherService:
    """전표 서비스 - CRUD + 자동 분개 생성"""

    def __init__(self):
        self.repo = VoucherRepository()
        self.account_repo = AccountRepository()
        self.journal_repo = JournalRepository()

    def _calculate_item_amounts(self, item_data: dict) -> dict:
        """항목 금액 계산: supply_price, tax_amount, total_amount"""
        quantity = item_data["quantity"]
        unit_price = item_data["unit_price"]
        supply_price = round(quantity * unit_price, 2)
        tax_amount = round(supply_price * 0.1, 2)
        total_amount = supply_price + tax_amount

        item_data["supply_price"] = supply_price
        item_data["tax_amount"] = tax_amount
        item_data["total_amount"] = total_amount
        return item_data

    def _prepare_items(self, items) -> List[dict]:
        """VoucherItemCreate 목록을 dict 목록으로 변환 + 금액 계산"""
        result = []
        for item in items:
            item_dict = {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "spec": item.spec,
                "unit": item.unit,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "memo": item.memo,
            }
            result.append(self._calculate_item_amounts(item_dict))
        return result

    async def _check_period_open(
        self, session: AsyncSession, voucher_date: date
    ) -> None:
        """마감된 기간인지 확인. 마감 시 ValueError 발생."""
        year = voucher_date.year
        month = voucher_date.month

        result = await session.execute(
            text(
                "SELECT is_closed FROM erp_business_periods "
                "WHERE year = :year AND month = :month"
            ),
            {"year": year, "month": month},
        )
        row = result.fetchone()

        if row and row[0]:
            raise ValueError(
                f"해당 기간({year}-{month:02d})은 마감되었습니다. "
                f"전표를 생성/수정할 수 없습니다."
            )

    async def list_vouchers(
        self,
        session: AsyncSession,
        filters: VoucherFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """전표 목록 조회"""
        return await self.repo.list(session, filters, skip, limit)

    async def get_voucher(
        self, session: AsyncSession, id: str
    ) -> Optional[dict]:
        """전표 상세 조회 (items 포함)"""
        return await self.repo.get(session, id)

    async def create_voucher(
        self, session: AsyncSession, data: VoucherCreate
    ) -> dict:
        """
        전표 생성

        1. 기간 마감 여부 확인
        2. 항목별 금액 계산 (supply_price, tax_amount, total_amount)
        3. 헤더 + 항목 DB INSERT
        4. 전표번호 자동 생성 (DB 함수)
        """
        await self._check_period_open(session, data.voucher_date)

        voucher_data = {
            "voucher_type": data.voucher_type.value,
            "voucher_date": data.voucher_date,
            "customer_id": data.customer_id,
            "employee_id": data.employee_id,
            "payment_method": data.payment_method.value if data.payment_method else None,
            "bank_account_id": data.bank_account_id,
            "memo": data.memo,
        }

        items_data = self._prepare_items(data.items)

        return await self.repo.create(session, voucher_data, items_data)

    async def update_voucher(
        self, session: AsyncSession, id: str, data: VoucherUpdate
    ) -> Optional[dict]:
        """
        전표 수정 (draft 상태만)

        items가 제공되면: 기존 항목 전체 삭제 → 새 항목 생성
        """
        existing = await self.repo.get(session, id)
        if not existing:
            return None

        if existing["status"] != "draft":
            raise ValueError(
                f"수정할 수 없는 상태입니다: {existing['status']} "
                f"(draft만 수정 가능)"
            )

        # 기간 마감 확인: 기존 전표 날짜
        existing_date = existing["voucher_date"]
        if isinstance(existing_date, str):
            existing_date = date.fromisoformat(existing_date)
        await self._check_period_open(session, existing_date)

        # 기간 마감 확인: 변경될 날짜 (다른 기간으로 이동하는 경우)
        if data.voucher_date is not None and data.voucher_date != existing_date:
            await self._check_period_open(session, data.voucher_date)

        update_dict = {}

        if data.voucher_date is not None:
            update_dict["voucher_date"] = data.voucher_date
        if data.customer_id is not None:
            update_dict["customer_id"] = data.customer_id
        if data.employee_id is not None:
            update_dict["employee_id"] = data.employee_id
        if data.payment_method is not None:
            update_dict["payment_method"] = data.payment_method.value
        if data.bank_account_id is not None:
            update_dict["bank_account_id"] = data.bank_account_id
        if data.memo is not None:
            update_dict["memo"] = data.memo

        # 항목이 변경되면 전체 교체
        if data.items is not None:
            items_data = self._prepare_items(data.items)

            # 합계 재계산
            supply_total = sum(i["supply_price"] for i in items_data)
            tax_total = sum(i["tax_amount"] for i in items_data)
            total = supply_total + tax_total

            update_dict["supply_amount"] = supply_total
            update_dict["tax_amount"] = tax_total
            update_dict["total_amount"] = total
            update_dict["unpaid_amount"] = total

            # 기존 항목 삭제 → 새 항목 생성
            await self.repo.delete_items(session, id)
            await self.repo._insert_items(session, id, items_data)

        if update_dict:
            result = await self.repo.update_header(session, id, update_dict)
            if not result:
                return None

        return await self.repo.get(session, id)

    async def delete_voucher(
        self, session: AsyncSession, id: str
    ) -> bool:
        """전표 삭제 (draft 상태만)"""
        existing = await self.repo.get(session, id)
        if not existing:
            raise ValueError(f"전표 ID '{id}'을(를) 찾을 수 없습니다")

        if existing["status"] != "draft":
            raise ValueError(
                f"삭제할 수 없는 상태입니다: {existing['status']} "
                f"(draft만 삭제 가능)"
            )

        return await self.repo.delete(session, id)

    async def confirm_voucher(
        self, session: AsyncSession, id: str
    ) -> dict:
        """
        전표 확정 (draft → confirmed) + 자동 분개 생성

        1. 상태 변경
        2. 전표 유형에 따른 분개 자동 생성
        3. 분개 즉시 전기 (posted)
        """
        existing = await self.repo.get(session, id)
        if not existing:
            raise ValueError(f"전표 ID '{id}'을(를) 찾을 수 없습니다")

        if existing["status"] != "draft":
            raise ValueError(
                f"확정할 수 없는 상태입니다: {existing['status']} "
                f"(draft만 확정 가능)"
            )

        # 1. 상태 변경
        result = await self.repo.update_status(session, id, "confirmed")
        if not result:
            raise RuntimeError("전표 상태 변경 실패")

        # 2. 자동 분개 생성
        await self._create_auto_journal(session, existing)

        # 3. 전체 데이터 반환
        return await self.repo.get(session, id)

    async def cancel_voucher(
        self, session: AsyncSession, id: str
    ) -> dict:
        """
        전표 취소 (confirmed → cancelled)

        분개는 JournalService.cancel_entry()와 동일하게
        역분개가 자동 생성됨 (분개장에서 처리)
        """
        existing = await self.repo.get(session, id)
        if not existing:
            raise ValueError(f"전표 ID '{id}'을(를) 찾을 수 없습니다")

        if existing["status"] != "confirmed":
            raise ValueError(
                f"취소할 수 없는 상태입니다: {existing['status']} "
                f"(confirmed만 취소 가능)"
            )

        # 1. 전표 상태 변경
        result = await self.repo.update_status(session, id, "cancelled")
        if not result:
            raise RuntimeError("전표 상태 변경 실패")

        # 2. 연결된 분개 취소 (역분개 자동 생성)
        await self._cancel_linked_journals(session, id)

        return await self.repo.get(session, id)

    async def _get_account_id_by_code(
        self, session: AsyncSession, code: str
    ) -> str:
        """계정과목 코드로 ID 조회"""
        account = await self.account_repo.get_by_code(session, code)
        if not account:
            raise ValueError(f"계정과목 코드 '{code}'을(를) 찾을 수 없습니다")
        return account["id"]

    async def _create_auto_journal(
        self, session: AsyncSession, voucher: dict
    ) -> dict:
        """
        전표 유형에 따른 자동 분개 생성

        매출: DR 매출채권(공급가+세액) / CR 상품매출(공급가) + CR 부가세예수금(세액)
        매입: DR 상품매입(공급가) + DR 부가세대급금(세액) / CR 매입채무(총액)
        수금: DR 현금/예금(총액) / CR 매출채권(총액)
        지급: DR 매입채무(총액) / CR 현금/예금(총액)
        지출: DR 기타비용(총액) / CR 현금/예금(총액)
        """
        v_type = voucher["voucher_type"]
        supply = float(voucher["supply_amount"])
        tax = float(voucher["tax_amount"])
        total = float(voucher["total_amount"])
        payment_method = voucher.get("payment_method") or "cash"

        journal_items = []

        if v_type == "sales":
            # DR: 매출채권 = 총액 (공급가 + 부가세)
            acc_1100 = await self._get_account_id_by_code(session, "1100")
            journal_items.append({
                "account_id": acc_1100,
                "debit": total,
                "credit": 0.0,
                "customer_id": voucher.get("customer_id"),
                "description": f"매출채권 - {voucher['voucher_no']}",
            })
            # CR: 상품매출 = 공급가
            acc_4100 = await self._get_account_id_by_code(session, "4100")
            journal_items.append({
                "account_id": acc_4100,
                "debit": 0.0,
                "credit": supply,
                "customer_id": voucher.get("customer_id"),
                "description": f"상품매출 - {voucher['voucher_no']}",
            })
            # CR: 부가세예수금 = 세액
            if tax > 0:
                acc_2400 = await self._get_account_id_by_code(session, "2400")
                journal_items.append({
                    "account_id": acc_2400,
                    "debit": 0.0,
                    "credit": tax,
                    "description": f"부가세예수금 - {voucher['voucher_no']}",
                })

        elif v_type == "purchase":
            # DR: 상품매입 = 공급가
            acc_5100 = await self._get_account_id_by_code(session, "5100")
            journal_items.append({
                "account_id": acc_5100,
                "debit": supply,
                "credit": 0.0,
                "description": f"상품매입 - {voucher['voucher_no']}",
            })
            # DR: 부가세대급금 = 세액
            if tax > 0:
                acc_1400 = await self._get_account_id_by_code(session, "1400")
                journal_items.append({
                    "account_id": acc_1400,
                    "debit": tax,
                    "credit": 0.0,
                    "description": f"부가세대급금 - {voucher['voucher_no']}",
                })
            # CR: 매입채무 = 총액
            acc_2100 = await self._get_account_id_by_code(session, "2100")
            journal_items.append({
                "account_id": acc_2100,
                "debit": 0.0,
                "credit": total,
                "customer_id": voucher.get("customer_id"),
                "description": f"매입채무 - {voucher['voucher_no']}",
            })

        elif v_type == "receipt":
            # DR: 현금/예금 = 총액
            cash_code = self._get_cash_account_code(payment_method)
            acc_cash = await self._get_account_id_by_code(session, cash_code)
            journal_items.append({
                "account_id": acc_cash,
                "debit": total,
                "credit": 0.0,
                "description": f"수금 - {voucher['voucher_no']}",
            })
            # CR: 매출채권 = 총액
            acc_1100 = await self._get_account_id_by_code(session, "1100")
            journal_items.append({
                "account_id": acc_1100,
                "debit": 0.0,
                "credit": total,
                "customer_id": voucher.get("customer_id"),
                "description": f"매출채권 회수 - {voucher['voucher_no']}",
            })

        elif v_type == "payment":
            # DR: 매입채무 = 총액
            acc_2100 = await self._get_account_id_by_code(session, "2100")
            journal_items.append({
                "account_id": acc_2100,
                "debit": total,
                "credit": 0.0,
                "customer_id": voucher.get("customer_id"),
                "description": f"매입채무 상환 - {voucher['voucher_no']}",
            })
            # CR: 현금/예금 = 총액
            cash_code = self._get_cash_account_code(payment_method)
            acc_cash = await self._get_account_id_by_code(session, cash_code)
            journal_items.append({
                "account_id": acc_cash,
                "debit": 0.0,
                "credit": total,
                "description": f"지급 - {voucher['voucher_no']}",
            })

        elif v_type == "expense":
            # DR: 잡손실(기타비용) = 총액
            acc_5990 = await self._get_account_id_by_code(session, "5990")
            journal_items.append({
                "account_id": acc_5990,
                "debit": total,
                "credit": 0.0,
                "description": f"경비지출 - {voucher['voucher_no']}",
            })
            # CR: 현금/예금 = 총액
            cash_code = self._get_cash_account_code(payment_method)
            acc_cash = await self._get_account_id_by_code(session, cash_code)
            journal_items.append({
                "account_id": acc_cash,
                "debit": 0.0,
                "credit": total,
                "description": f"경비지급 - {voucher['voucher_no']}",
            })

        if not journal_items:
            return {}

        # 분개 생성
        entry_data = {
            "entry_date": voucher["voucher_date"],
            "narration": f"[자동분개] {voucher['voucher_no']} - {v_type}",
            "voucher_id": voucher["id"],
        }

        journal = await self.journal_repo.create_entry(
            session, entry_data, journal_items
        )

        # 즉시 전기
        await self.journal_repo.update_status(session, journal["id"], "posted")

        return journal

    def _get_cash_account_code(self, payment_method: str) -> str:
        """결제수단에 따른 현금/예금 계정코드 반환"""
        method_map = {
            "cash": "1010",
            "bank_transfer": "1020",
            "check": "1010",
            "card": "1020",
            "note": "1010",
        }
        return method_map.get(payment_method, "1010")

    async def _cancel_linked_journals(
        self, session: AsyncSession, voucher_id: str
    ) -> None:
        """전표에 연결된 분개를 취소 (역분개 자동 생성)"""
        from kis_erp_core.models.accounting_models import JournalEntryFilter

        filters = JournalEntryFilter(voucher_id=voucher_id)
        entries = await self.journal_repo.list(session, filters, skip=0, limit=100)

        for entry in entries:
            if entry.get("status") == "posted":
                full_entry = await self.journal_repo.get(session, entry["id"])
                if not full_entry:
                    continue

                # 역분개 생성 (차변/대변 반전)
                reverse_items = []
                for item in full_entry.get("items", []):
                    reverse_items.append({
                        "account_id": item["account_id"],
                        "debit": float(item["credit"]),
                        "credit": float(item["debit"]),
                        "customer_id": item.get("customer_id"),
                        "description": f"[역분개] {item.get('description') or ''}".strip(),
                    })

                # 원래 분개 취소
                await self.journal_repo.update_status(
                    session, entry["id"], "cancelled"
                )

                # 역분개 생성 + 전기
                reverse_data = {
                    "entry_date": full_entry["entry_date"],
                    "narration": f"[역분개] {full_entry['narration']}",
                    "voucher_id": voucher_id,
                }
                reverse = await self.journal_repo.create_entry(
                    session, reverse_data, reverse_items
                )
                await self.journal_repo.update_status(
                    session, reverse["id"], "posted"
                )
