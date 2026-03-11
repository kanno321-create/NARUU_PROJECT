"""
ERP Service - ERP 시스템 연동 서비스

발주, 재고, 주문, 고객 관리 기능:
- 발주 등록 (Order Registration)
- 재고 확인 (Inventory Check)
- 주문 조회 (Order Query)
- 고객 관리 (Customer Management) - 업체명/연락처/이메일/주소

참고: CLAUDE.md에 따르면 ERP는 별도 AI 시스템이 담당
이 서비스는 해당 시스템과의 인터페이스 역할 수행
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# 고객(Customer) 관련 모델
# ============================================================================


@dataclass
class Customer:
    """고객 정보 (견적 연동용)"""
    customer_id: str  # 고객 ID (자동 생성)
    company_name: str  # 업체명 (필수)
    contact_name: str | None = None  # 담당자명
    phone: str | None = None  # 연락처
    email: str | None = None  # 이메일
    address: str | None = None  # 주소
    business_number: str | None = None  # 사업자번호
    notes: str = ""  # 비고
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str | None = None


class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING = "pending"  # 대기
    CONFIRMED = "confirmed"  # 확정
    IN_PROGRESS = "in_progress"  # 진행중
    SHIPPED = "shipped"  # 출하
    DELIVERED = "delivered"  # 완료
    CANCELLED = "cancelled"  # 취소


class ERPOperation(str, Enum):
    """ERP 작업 유형"""
    ORDER_CREATE = "order_create"  # 발주 등록
    ORDER_QUERY = "order_query"  # 주문 조회
    ORDER_UPDATE = "order_update"  # 주문 수정
    ORDER_CANCEL = "order_cancel"  # 주문 취소
    INVENTORY_CHECK = "inventory_check"  # 재고 확인
    INVENTORY_RESERVE = "inventory_reserve"  # 재고 예약


@dataclass
class OrderItem:
    """발주 품목"""
    sku: str  # 품목 코드
    name: str  # 품목명
    quantity: int  # 수량
    unit_price: int  # 단가 (원)
    subtotal: int = field(init=False)  # 소계

    def __post_init__(self):
        self.subtotal = self.quantity * self.unit_price


@dataclass
class Order:
    """발주 데이터"""
    order_id: str
    estimate_id: str | None = None
    customer_name: str = ""
    items: list[OrderItem] = field(default_factory=list)
    total_amount: int = 0
    status: OrderStatus = OrderStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str | None = None
    notes: str = ""


@dataclass
class InventoryItem:
    """재고 품목"""
    sku: str  # 품목 코드
    name: str  # 품목명
    available_qty: int  # 가용 재고
    reserved_qty: int = 0  # 예약 재고
    location: str = "main_warehouse"  # 위치
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ERPResult:
    """ERP 작업 결과"""
    success: bool
    operation: ERPOperation
    message: str
    data: dict | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ERPConfig:
    """ERP 설정"""
    api_base_url: str = os.getenv("ERP_API_URL", "http://localhost:9000/api/erp")
    api_key: str = os.getenv("ERP_API_KEY", "")
    timeout: int = int(os.getenv("ERP_TIMEOUT", "30"))
    # ERP AI 연동 설정 (별도 AI 시스템)
    erp_ai_enabled: bool = os.getenv("ERP_AI_ENABLED", "false").lower() == "true"


class ERPService:
    """ERP 시스템 연동 서비스"""

    def __init__(self, config: ERPConfig | None = None):
        """초기화"""
        self.config = config or ERPConfig()
        self._orders: dict[str, Order] = {}  # 임시 메모리 저장소 (실제로는 DB 연동)
        self._inventory: dict[str, InventoryItem] = self._init_sample_inventory()
        self._customers: dict[str, Customer] = self._init_sample_customers()
        logger.info(f"ERP Service initialized (AI enabled: {self.config.erp_ai_enabled})")

    def _init_sample_inventory(self) -> dict[str, InventoryItem]:
        """샘플 재고 데이터 초기화 (실제로는 DB에서 로드)"""
        items = [
            InventoryItem(sku="SBE-104", name="상도 배선용차단기 4P 100AF", available_qty=50),
            InventoryItem(sku="SBE-53", name="상도 배선용차단기 3P 50AF", available_qty=100),
            InventoryItem(sku="SEE-104", name="상도 누전차단기 4P 100AF", available_qty=30),
            InventoryItem(sku="SEE-32", name="상도 누전차단기 2P 30AF", available_qty=200),
            InventoryItem(sku="ENC-600800", name="옥내노출외함 600x800x200", available_qty=20),
            InventoryItem(sku="ENC-700900", name="옥내노출외함 700x900x200", available_qty=15),
            InventoryItem(sku="ET-100", name="E.T 100AF용", available_qty=500),
            InventoryItem(sku="NT-001", name="N.T 표준형", available_qty=500),
            InventoryItem(sku="BUSBAR-3T15", name="BUS-BAR 3T×15", available_qty=100),
            InventoryItem(sku="PCOVER-STD", name="P-COVER 아크릴", available_qty=50),
        ]
        return {item.sku: item for item in items}

    def _init_sample_customers(self) -> dict[str, Customer]:
        """샘플 고객 데이터 초기화 (실제로는 DB에서 로드)"""
        customers = [
            Customer(
                customer_id="CUS-001",
                company_name="(주)한국전기",
                contact_name="김철수",
                phone="02-1234-5678",
                email="kim@hkelec.com",
                address="서울시 강남구 테헤란로 123",
                business_number="123-45-67890",
                notes="VIP 고객"
            ),
            Customer(
                customer_id="CUS-002",
                company_name="대한전력설비(주)",
                contact_name="이영희",
                phone="031-987-6543",
                email="lee@dhpower.co.kr",
                address="경기도 성남시 분당구 판교로 456",
                business_number="234-56-78901",
                notes=""
            ),
            Customer(
                customer_id="CUS-003",
                company_name="삼성전기공사",
                contact_name="박지민",
                phone="032-555-1234",
                email="park@sselec.com",
                address="인천시 남동구 공단로 789",
                business_number="345-67-89012",
                notes="대량 발주 고객"
            ),
            Customer(
                customer_id="CUS-004",
                company_name="동양전기산업",
                contact_name="최동훈",
                phone="051-234-5678",
                email="choi@dongyang.kr",
                address="부산시 해운대구 센텀로 321",
                business_number="456-78-90123",
                notes=""
            ),
            Customer(
                customer_id="CUS-005",
                company_name="서울배전반",
                contact_name="정수진",
                phone="02-789-0123",
                email="jung@seoulpanel.co.kr",
                address="서울시 금천구 가산디지털로 654",
                business_number="567-89-01234",
                notes="정기 거래처"
            ),
        ]
        return {c.customer_id: c for c in customers}

    async def create_order(
        self,
        estimate_id: str | None = None,
        customer_name: str = "",
        items: list[dict] | None = None,
        notes: str = ""
    ) -> ERPResult:
        """
        발주 등록

        Args:
            estimate_id: 견적 ID (선택)
            customer_name: 고객명
            items: 발주 품목 목록 [{sku, name, quantity, unit_price}]
            notes: 비고

        Returns:
            ERPResult: 발주 결과
        """
        try:
            # 주문 ID 생성
            order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 품목 변환
            order_items = []
            total_amount = 0

            if items:
                for item_data in items:
                    order_item = OrderItem(
                        sku=item_data.get("sku", ""),
                        name=item_data.get("name", ""),
                        quantity=item_data.get("quantity", 1),
                        unit_price=item_data.get("unit_price", 0)
                    )
                    order_items.append(order_item)
                    total_amount += order_item.subtotal

            # 주문 생성
            order = Order(
                order_id=order_id,
                estimate_id=estimate_id,
                customer_name=customer_name,
                items=order_items,
                total_amount=total_amount,
                status=OrderStatus.PENDING,
                notes=notes
            )

            # 저장 (임시 메모리, 실제로는 DB)
            self._orders[order_id] = order

            logger.info(f"Order created: {order_id}")

            return ERPResult(
                success=True,
                operation=ERPOperation.ORDER_CREATE,
                message="발주가 성공적으로 등록되었습니다.",
                data={
                    "order_id": order_id,
                    "estimate_id": estimate_id,
                    "customer_name": customer_name,
                    "total_amount": total_amount,
                    "item_count": len(order_items),
                    "status": OrderStatus.PENDING.value
                }
            )

        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            return ERPResult(
                success=False,
                operation=ERPOperation.ORDER_CREATE,
                message="발주 등록에 실패했습니다.",
                error=str(e)
            )

    async def check_inventory(
        self,
        sku: str | None = None,
        category: str | None = None
    ) -> ERPResult:
        """
        재고 확인

        Args:
            sku: 품목 코드 (특정 품목 조회)
            category: 카테고리 (차단기, 외함 등)

        Returns:
            ERPResult: 재고 조회 결과
        """
        try:
            if sku:
                # 특정 품목 조회
                item = self._inventory.get(sku)
                if not item:
                    return ERPResult(
                        success=False,
                        operation=ERPOperation.INVENTORY_CHECK,
                        message=f"품목을 찾을 수 없습니다: {sku}",
                        error="ITEM_NOT_FOUND"
                    )

                return ERPResult(
                    success=True,
                    operation=ERPOperation.INVENTORY_CHECK,
                    message="재고 조회 완료",
                    data={
                        "sku": item.sku,
                        "name": item.name,
                        "available_qty": item.available_qty,
                        "reserved_qty": item.reserved_qty,
                        "location": item.location,
                        "last_updated": item.last_updated
                    }
                )
            else:
                # 전체 또는 카테고리별 조회
                inventory_list = []
                for item in self._inventory.values():
                    if category:
                        # 카테고리 필터 (간단 구현)
                        if category == "차단기" and "차단기" in item.name:
                            inventory_list.append(item)
                        elif category == "외함" and "외함" in item.name:
                            inventory_list.append(item)
                        elif category == "부속" and item.sku.startswith(("ET-", "NT-", "BUS", "PCOVER")):
                            inventory_list.append(item)
                    else:
                        inventory_list.append(item)

                return ERPResult(
                    success=True,
                    operation=ERPOperation.INVENTORY_CHECK,
                    message=f"재고 조회 완료 ({len(inventory_list)}개 품목)",
                    data={
                        "items": [
                            {
                                "sku": item.sku,
                                "name": item.name,
                                "available_qty": item.available_qty,
                                "reserved_qty": item.reserved_qty,
                            }
                            for item in inventory_list
                        ],
                        "total_count": len(inventory_list)
                    }
                )

        except Exception as e:
            logger.error(f"Inventory check failed: {e}")
            return ERPResult(
                success=False,
                operation=ERPOperation.INVENTORY_CHECK,
                message="재고 조회에 실패했습니다.",
                error=str(e)
            )

    async def get_orders(
        self,
        order_id: str | None = None,
        estimate_id: str | None = None,
        status: OrderStatus | None = None,
        limit: int = 10
    ) -> ERPResult:
        """
        주문 조회

        Args:
            order_id: 주문 ID (특정 주문 조회)
            estimate_id: 견적 ID (견적 기반 조회)
            status: 주문 상태 필터
            limit: 최대 결과 수

        Returns:
            ERPResult: 주문 조회 결과
        """
        try:
            if order_id:
                # 특정 주문 조회
                order = self._orders.get(order_id)
                if not order:
                    return ERPResult(
                        success=False,
                        operation=ERPOperation.ORDER_QUERY,
                        message=f"주문을 찾을 수 없습니다: {order_id}",
                        error="ORDER_NOT_FOUND"
                    )

                return ERPResult(
                    success=True,
                    operation=ERPOperation.ORDER_QUERY,
                    message="주문 조회 완료",
                    data={
                        "order_id": order.order_id,
                        "estimate_id": order.estimate_id,
                        "customer_name": order.customer_name,
                        "total_amount": order.total_amount,
                        "status": order.status.value,
                        "item_count": len(order.items),
                        "created_at": order.created_at,
                        "notes": order.notes
                    }
                )
            else:
                # 목록 조회
                orders_list = list(self._orders.values())

                # 필터 적용
                if estimate_id:
                    orders_list = [o for o in orders_list if o.estimate_id == estimate_id]
                if status:
                    orders_list = [o for o in orders_list if o.status == status]

                # 최근순 정렬 및 제한
                orders_list = sorted(orders_list, key=lambda x: x.created_at, reverse=True)[:limit]

                return ERPResult(
                    success=True,
                    operation=ERPOperation.ORDER_QUERY,
                    message=f"주문 조회 완료 ({len(orders_list)}건)",
                    data={
                        "orders": [
                            {
                                "order_id": o.order_id,
                                "estimate_id": o.estimate_id,
                                "customer_name": o.customer_name,
                                "total_amount": o.total_amount,
                                "status": o.status.value,
                                "created_at": o.created_at
                            }
                            for o in orders_list
                        ],
                        "total_count": len(orders_list)
                    }
                )

        except Exception as e:
            logger.error(f"Order query failed: {e}")
            return ERPResult(
                success=False,
                operation=ERPOperation.ORDER_QUERY,
                message="주문 조회에 실패했습니다.",
                error=str(e)
            )

    async def cancel_order(self, order_id: str, reason: str = "") -> ERPResult:
        """
        주문 취소

        Args:
            order_id: 주문 ID
            reason: 취소 사유

        Returns:
            ERPResult: 취소 결과
        """
        try:
            order = self._orders.get(order_id)
            if not order:
                return ERPResult(
                    success=False,
                    operation=ERPOperation.ORDER_CANCEL,
                    message=f"주문을 찾을 수 없습니다: {order_id}",
                    error="ORDER_NOT_FOUND"
                )

            # 취소 가능 상태 확인
            if order.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
                return ERPResult(
                    success=False,
                    operation=ERPOperation.ORDER_CANCEL,
                    message=f"이미 출하된 주문은 취소할 수 없습니다. (현재 상태: {order.status.value})",
                    error="CANNOT_CANCEL"
                )

            # 취소 처리
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now(UTC).isoformat()
            order.notes = f"{order.notes}\n취소 사유: {reason}" if reason else order.notes

            logger.info(f"Order cancelled: {order_id}")

            return ERPResult(
                success=True,
                operation=ERPOperation.ORDER_CANCEL,
                message="주문이 취소되었습니다.",
                data={
                    "order_id": order_id,
                    "status": OrderStatus.CANCELLED.value,
                    "cancelled_at": order.updated_at,
                    "reason": reason
                }
            )

        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            return ERPResult(
                success=False,
                operation=ERPOperation.ORDER_CANCEL,
                message="주문 취소에 실패했습니다.",
                error=str(e)
            )

    # ========================================================================
    # 고객 관리 (Customer Management)
    # ========================================================================

    async def create_customer(
        self,
        company_name: str,
        contact_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        business_number: str | None = None,
        notes: str = ""
    ) -> dict:
        """
        고객 등록

        Args:
            company_name: 업체명 (필수)
            contact_name: 담당자명
            phone: 연락처
            email: 이메일
            address: 주소
            business_number: 사업자번호
            notes: 비고

        Returns:
            등록된 고객 정보
        """
        try:
            # 고객 ID 생성
            customer_id = f"CUS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            customer = Customer(
                customer_id=customer_id,
                company_name=company_name,
                contact_name=contact_name,
                phone=phone,
                email=email,
                address=address,
                business_number=business_number,
                notes=notes
            )

            # 저장 (임시 메모리, 실제로는 DB)
            self._customers[customer_id] = customer

            logger.info(f"Customer created: {customer_id} - {company_name}")

            return {
                "success": True,
                "message": "고객이 등록되었습니다.",
                "data": {
                    "customer_id": customer_id,
                    "company_name": company_name,
                    "contact_name": contact_name,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "business_number": business_number,
                    "created_at": customer.created_at
                }
            }

        except Exception as e:
            logger.error(f"Customer creation failed: {e}")
            return {
                "success": False,
                "message": "고객 등록에 실패했습니다.",
                "error": str(e)
            }

    async def search_customers(
        self,
        query: str | None = None,
        limit: int = 10
    ) -> dict:
        """
        고객 검색 (자동완성용)

        Args:
            query: 검색어 (업체명, 담당자명, 연락처, 이메일 부분 일치)
            limit: 최대 결과 수

        Returns:
            검색 결과 (자동완성 리스트)
        """
        try:
            results = []

            for customer in self._customers.values():
                if query:
                    query_lower = query.lower()
                    # 업체명, 담당자명, 연락처, 이메일에서 검색
                    match = False
                    if customer.company_name and query_lower in customer.company_name.lower():
                        match = True
                    elif customer.contact_name and query_lower in customer.contact_name.lower():
                        match = True
                    elif customer.phone and query_lower in customer.phone:
                        match = True
                    elif customer.email and query_lower in customer.email.lower():
                        match = True

                    if match:
                        results.append(customer)
                else:
                    results.append(customer)

            # 최근 등록순 정렬 및 제한
            results = sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]

            return {
                "success": True,
                "message": f"고객 검색 완료 ({len(results)}건)",
                "data": {
                    "customers": [
                        {
                            "customer_id": c.customer_id,
                            "company_name": c.company_name,
                            "contact_name": c.contact_name,
                            "phone": c.phone,
                            "email": c.email,
                            "address": c.address,
                            "business_number": c.business_number,
                        }
                        for c in results
                    ],
                    "total_count": len(results)
                }
            }

        except Exception as e:
            logger.error(f"Customer search failed: {e}")
            return {
                "success": False,
                "message": "고객 검색에 실패했습니다.",
                "error": str(e)
            }

    async def get_customer(self, customer_id: str) -> dict:
        """
        고객 상세 조회

        Args:
            customer_id: 고객 ID

        Returns:
            고객 상세 정보
        """
        try:
            customer = self._customers.get(customer_id)
            if not customer:
                return {
                    "success": False,
                    "message": f"고객을 찾을 수 없습니다: {customer_id}",
                    "error": "CUSTOMER_NOT_FOUND"
                }

            return {
                "success": True,
                "message": "고객 조회 완료",
                "data": {
                    "customer_id": customer.customer_id,
                    "company_name": customer.company_name,
                    "contact_name": customer.contact_name,
                    "phone": customer.phone,
                    "email": customer.email,
                    "address": customer.address,
                    "business_number": customer.business_number,
                    "notes": customer.notes,
                    "created_at": customer.created_at,
                    "updated_at": customer.updated_at
                }
            }

        except Exception as e:
            logger.error(f"Customer get failed: {e}")
            return {
                "success": False,
                "message": "고객 조회에 실패했습니다.",
                "error": str(e)
            }

    async def update_customer(
        self,
        customer_id: str,
        company_name: str | None = None,
        contact_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        business_number: str | None = None,
        notes: str | None = None
    ) -> dict:
        """
        고객 정보 수정

        Args:
            customer_id: 고객 ID
            (기타): 수정할 필드들

        Returns:
            수정된 고객 정보
        """
        try:
            customer = self._customers.get(customer_id)
            if not customer:
                return {
                    "success": False,
                    "message": f"고객을 찾을 수 없습니다: {customer_id}",
                    "error": "CUSTOMER_NOT_FOUND"
                }

            # 필드 업데이트
            if company_name is not None:
                customer.company_name = company_name
            if contact_name is not None:
                customer.contact_name = contact_name
            if phone is not None:
                customer.phone = phone
            if email is not None:
                customer.email = email
            if address is not None:
                customer.address = address
            if business_number is not None:
                customer.business_number = business_number
            if notes is not None:
                customer.notes = notes

            customer.updated_at = datetime.now(UTC).isoformat()

            logger.info(f"Customer updated: {customer_id}")

            return {
                "success": True,
                "message": "고객 정보가 수정되었습니다.",
                "data": {
                    "customer_id": customer.customer_id,
                    "company_name": customer.company_name,
                    "contact_name": customer.contact_name,
                    "phone": customer.phone,
                    "email": customer.email,
                    "address": customer.address,
                    "updated_at": customer.updated_at
                }
            }

        except Exception as e:
            logger.error(f"Customer update failed: {e}")
            return {
                "success": False,
                "message": "고객 정보 수정에 실패했습니다.",
                "error": str(e)
            }


# 싱글톤 인스턴스
_erp_service: ERPService | None = None


def get_erp_service() -> ERPService:
    """ERPService 싱글톤"""
    global _erp_service
    if _erp_service is None:
        _erp_service = ERPService()
    return _erp_service
