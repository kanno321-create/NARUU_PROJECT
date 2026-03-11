import { NextRequest, NextResponse } from "next/server";

// 고객 타입
interface Customer {
    id: string;
    name: string;
    businessNumber: string;
    representative: string;
    businessType: string;
    businessCategory: string;
    phone: string;
    fax?: string;
    email?: string;
    address: string;
    addressDetail?: string;
    bankAccount?: {
        bank: string;
        accountNumber: string;
        accountHolder: string;
    };
    creditLimit?: number;
    receivables: number;
    payables: number;
    lastTransactionDate?: string;
    notes?: string;
    status: "active" | "inactive" | "suspended";
    createdAt: string;
    updatedAt: string;
}

// 샘플 고객 데이터
let customers: Customer[] = [
    {
        id: "c1",
        name: "동양기전(주)",
        businessNumber: "123-45-67890",
        representative: "김철수",
        businessType: "제조업",
        businessCategory: "전기기기 제조",
        phone: "02-1234-5678",
        fax: "02-1234-5679",
        email: "contact@dongyang.co.kr",
        address: "서울특별시 강남구 테헤란로 123",
        addressDetail: "동양빌딩 5층",
        bankAccount: {
            bank: "우리은행",
            accountNumber: "1002-123-456789",
            accountHolder: "동양기전(주)",
        },
        creditLimit: 50000000,
        receivables: 2500000,
        payables: 0,
        lastTransactionDate: new Date().toISOString(),
        status: "active",
        createdAt: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: "c2",
        name: "삼성전자",
        businessNumber: "124-81-00998",
        representative: "이재용",
        businessType: "제조업",
        businessCategory: "전자제품 제조",
        phone: "02-2255-0114",
        email: "business@samsung.com",
        address: "경기도 수원시 영통구 삼성로 129",
        creditLimit: 100000000,
        receivables: 1800000,
        payables: 500000,
        lastTransactionDate: new Date().toISOString(),
        status: "active",
        createdAt: new Date(Date.now() - 730 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: "c3",
        name: "LG전자",
        businessNumber: "107-86-14075",
        representative: "조주완",
        businessType: "제조업",
        businessCategory: "가전제품 제조",
        phone: "02-3777-1114",
        email: "business@lge.com",
        address: "서울특별시 영등포구 여의대로 128",
        creditLimit: 80000000,
        receivables: 3200000,
        payables: 0,
        lastTransactionDate: new Date(Date.now() - 86400000).toISOString(),
        status: "active",
        createdAt: new Date(Date.now() - 500 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
    },
    {
        id: "c4",
        name: "현대모비스",
        businessNumber: "132-81-00987",
        representative: "정의선",
        businessType: "제조업",
        businessCategory: "자동차 부품",
        phone: "02-2018-5000",
        email: "parts@mobis.co.kr",
        address: "서울특별시 강남구 테헤란로 203",
        creditLimit: 60000000,
        receivables: 0,
        payables: 2000000,
        lastTransactionDate: new Date(Date.now() - 86400000).toISOString(),
        status: "active",
        createdAt: new Date(Date.now() - 400 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
    },
    {
        id: "c5",
        name: "SK하이닉스",
        businessNumber: "140-81-01234",
        representative: "박정호",
        businessType: "제조업",
        businessCategory: "반도체 제조",
        phone: "031-8082-1114",
        email: "business@skhynix.com",
        address: "경기도 이천시 부발읍 경충대로 2091",
        creditLimit: 70000000,
        receivables: 4500000,
        payables: 0,
        lastTransactionDate: new Date(Date.now() - 172800000).toISOString(),
        notes: "미수금 주의 거래처",
        status: "active",
        createdAt: new Date(Date.now() - 300 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date(Date.now() - 172800000).toISOString(),
    },
    {
        id: "c6",
        name: "포스코",
        businessNumber: "101-81-45678",
        representative: "최정우",
        businessType: "제조업",
        businessCategory: "철강 제조",
        phone: "054-220-0114",
        email: "business@posco.com",
        address: "경상북도 포항시 남구 동해안로 6261",
        creditLimit: 90000000,
        receivables: 0,
        payables: 3500000,
        lastTransactionDate: new Date(Date.now() - 259200000).toISOString(),
        status: "active",
        createdAt: new Date(Date.now() - 600 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date(Date.now() - 259200000).toISOString(),
    },
    {
        id: "c7",
        name: "LG이노텍",
        businessNumber: "108-81-56789",
        representative: "정철동",
        businessType: "제조업",
        businessCategory: "전자부품 제조",
        phone: "02-3777-3500",
        email: "business@lginnotek.com",
        address: "서울특별시 강서구 마곡중앙8로 71",
        creditLimit: 55000000,
        receivables: 2800000,
        payables: 0,
        lastTransactionDate: new Date(Date.now() - 345600000).toISOString(),
        status: "active",
        createdAt: new Date(Date.now() - 450 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date(Date.now() - 345600000).toISOString(),
    },
    {
        id: "c8",
        name: "한화솔루션",
        businessNumber: "109-81-98765",
        representative: "김동관",
        businessType: "제조업",
        businessCategory: "화학제품 제조",
        phone: "02-729-1114",
        email: "business@hanwha.com",
        address: "서울특별시 중구 청계천로 86",
        creditLimit: 45000000,
        receivables: 0,
        payables: 1200000,
        lastTransactionDate: new Date(Date.now() - 432000000).toISOString(),
        status: "active",
        createdAt: new Date(Date.now() - 350 * 24 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date(Date.now() - 432000000).toISOString(),
    },
];

// GET: 고객 목록 조회
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const status = searchParams.get("status");
        const search = searchParams.get("search");
        const hasReceivables = searchParams.get("hasReceivables");
        const hasPayables = searchParams.get("hasPayables");
        const limit = parseInt(searchParams.get("limit") || "50");
        const offset = parseInt(searchParams.get("offset") || "0");

        let filteredCustomers = [...customers];

        // 상태 필터
        if (status) {
            filteredCustomers = filteredCustomers.filter(c => c.status === status);
        }

        // 검색 필터
        if (search) {
            const query = search.toLowerCase();
            filteredCustomers = filteredCustomers.filter(c =>
                c.name.toLowerCase().includes(query) ||
                c.businessNumber.includes(query) ||
                c.representative.toLowerCase().includes(query)
            );
        }

        // 미수금 있는 거래처
        if (hasReceivables === "true") {
            filteredCustomers = filteredCustomers.filter(c => c.receivables > 0);
        }

        // 미지급금 있는 거래처
        if (hasPayables === "true") {
            filteredCustomers = filteredCustomers.filter(c => c.payables > 0);
        }

        // 이름 오름차순 정렬
        filteredCustomers.sort((a, b) => a.name.localeCompare(b.name, "ko"));

        // 통계
        const stats = {
            total: customers.length,
            active: customers.filter(c => c.status === "active").length,
            inactive: customers.filter(c => c.status === "inactive").length,
            suspended: customers.filter(c => c.status === "suspended").length,
            totalReceivables: customers.reduce((sum, c) => sum + c.receivables, 0),
            totalPayables: customers.reduce((sum, c) => sum + c.payables, 0),
            withReceivables: customers.filter(c => c.receivables > 0).length,
            withPayables: customers.filter(c => c.payables > 0).length,
        };

        // 페이지네이션
        const total = filteredCustomers.length;
        const paginatedCustomers = filteredCustomers.slice(offset, offset + limit);

        return NextResponse.json({
            success: true,
            customers: paginatedCustomers,
            stats,
            pagination: {
                total,
                limit,
                offset,
                hasMore: offset + limit < total,
            },
        });
    } catch (error) {
        console.error("Customers GET error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to fetch customers" },
            { status: 500 }
        );
    }
}

// POST: 새 고객 생성
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        // 입력 유효성 검증
        if (!body.name || typeof body.name !== "string" || body.name.trim() === "") {
            return NextResponse.json(
                { success: false, error: "거래처명(name)은 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        if (!body.businessNumber || typeof body.businessNumber !== "string") {
            return NextResponse.json(
                { success: false, error: "사업자번호(businessNumber)는 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        // 사업자번호 형식 검증 (###-##-#####)
        const bizNumPattern = /^\d{3}-\d{2}-\d{5}$/;
        if (!bizNumPattern.test(body.businessNumber)) {
            return NextResponse.json(
                { success: false, error: "사업자번호 형식이 올바르지 않습니다 (예: 123-45-67890)", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        if (!body.representative || typeof body.representative !== "string" || body.representative.trim() === "") {
            return NextResponse.json(
                { success: false, error: "대표자명(representative)은 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        if (!body.phone || typeof body.phone !== "string") {
            return NextResponse.json(
                { success: false, error: "전화번호(phone)는 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        if (!body.address || typeof body.address !== "string" || body.address.trim() === "") {
            return NextResponse.json(
                { success: false, error: "주소(address)는 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        // 이메일 형식 검증 (선택 필드)
        if (body.email && typeof body.email === "string") {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(body.email)) {
                return NextResponse.json(
                    { success: false, error: "이메일 형식이 올바르지 않습니다", code: "E_VALIDATION" },
                    { status: 400 }
                );
            }
        }
        // 중복 사업자번호 검증
        const existingCustomer = customers.find(c => c.businessNumber === body.businessNumber);
        if (existingCustomer) {
            return NextResponse.json(
                { success: false, error: "이미 등록된 사업자번호입니다", code: "E_DUPLICATE" },
                { status: 409 }
            );
        }

        const newCustomer: Customer = {
            id: `c-${Date.now().toString().slice(-6)}`,
            name: body.name.trim(),
            businessNumber: body.businessNumber,
            representative: body.representative.trim(),
            businessType: body.businessType || "",
            businessCategory: body.businessCategory || "",
            phone: body.phone,
            fax: body.fax,
            email: body.email,
            address: body.address.trim(),
            addressDetail: body.addressDetail,
            bankAccount: body.bankAccount,
            creditLimit: body.creditLimit || 0,
            receivables: 0,
            payables: 0,
            notes: body.notes,
            status: "active",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };

        customers.push(newCustomer);

        return NextResponse.json({
            success: true,
            customer: newCustomer,
        });
    } catch (error) {
        console.error("Customers POST error:", error);
        return NextResponse.json(
            { success: false, error: "거래처 생성에 실패했습니다", code: "E_INTERNAL" },
            { status: 500 }
        );
    }
}

// PUT: 고객 수정
export async function PUT(request: NextRequest) {
    try {
        const body = await request.json();
        const { id, ...updates } = body;

        const customerIndex = customers.findIndex(c => c.id === id);
        if (customerIndex === -1) {
            return NextResponse.json(
                { success: false, error: "Customer not found" },
                { status: 404 }
            );
        }

        customers[customerIndex] = {
            ...customers[customerIndex],
            ...updates,
            updatedAt: new Date().toISOString(),
        };

        return NextResponse.json({
            success: true,
            customer: customers[customerIndex],
        });
    } catch (error) {
        console.error("Customers PUT error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to update customer" },
            { status: 500 }
        );
    }
}

// DELETE: 고객 삭제
export async function DELETE(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get("id");

        if (!id) {
            return NextResponse.json(
                { success: false, error: "Customer ID required" },
                { status: 400 }
            );
        }

        const customerIndex = customers.findIndex(c => c.id === id);
        if (customerIndex === -1) {
            return NextResponse.json(
                { success: false, error: "Customer not found" },
                { status: 404 }
            );
        }

        // 미수금/미지급금이 있는 경우 삭제 불가
        const customer = customers[customerIndex];
        if (customer.receivables > 0 || customer.payables > 0) {
            return NextResponse.json(
                {
                    success: false,
                    error: "미수금 또는 미지급금이 있는 거래처는 삭제할 수 없습니다.",
                },
                { status: 400 }
            );
        }

        customers.splice(customerIndex, 1);

        return NextResponse.json({
            success: true,
            message: "Customer deleted",
        });
    } catch (error) {
        console.error("Customers DELETE error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to delete customer" },
            { status: 500 }
        );
    }
}
