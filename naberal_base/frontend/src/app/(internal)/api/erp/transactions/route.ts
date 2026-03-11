import { NextRequest, NextResponse } from "next/server";

// 거래 타입
interface Transaction {
    id: string;
    date: string;
    customer: string;
    customerId: string;
    type: "sales" | "purchase" | "collection" | "payment";
    typeLabel: string;
    amount: number;
    status: "completed" | "pending" | "overdue";
    description?: string;
    items?: { name: string; quantity: number; unitPrice: number }[];
    createdAt: string;
    updatedAt: string;
}

// 샘플 거래 데이터
let transactions: Transaction[] = [
    {
        id: "TX-2024001",
        date: new Date().toISOString(),
        customer: "동양기전(주)",
        customerId: "c1",
        type: "sales",
        typeLabel: "매출",
        amount: 2500000,
        status: "completed",
        description: "분전반 납품",
        items: [
            { name: "분전반 400A", quantity: 1, unitPrice: 2000000 },
            { name: "차단기 100A", quantity: 5, unitPrice: 100000 },
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: "TX-2024002",
        date: new Date().toISOString(),
        customer: "삼성전자",
        customerId: "c2",
        type: "purchase",
        typeLabel: "매입",
        amount: 1800000,
        status: "pending",
        description: "자재 구매",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: "TX-2024003",
        date: new Date(Date.now() - 86400000).toISOString(),
        customer: "LG전자",
        customerId: "c3",
        type: "sales",
        typeLabel: "매출",
        amount: 3200000,
        status: "completed",
        description: "배전반 설치",
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
    },
    {
        id: "TX-2024004",
        date: new Date(Date.now() - 86400000).toISOString(),
        customer: "현대모비스",
        customerId: "c4",
        type: "collection",
        typeLabel: "수금",
        amount: 5000000,
        status: "completed",
        description: "미수금 회수",
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
    },
    {
        id: "TX-2024005",
        date: new Date(Date.now() - 172800000).toISOString(),
        customer: "SK하이닉스",
        customerId: "c5",
        type: "sales",
        typeLabel: "매출",
        amount: 4500000,
        status: "overdue",
        description: "전기 패널 납품 - 미수금",
        createdAt: new Date(Date.now() - 172800000).toISOString(),
        updatedAt: new Date(Date.now() - 172800000).toISOString(),
    },
    {
        id: "TX-2024006",
        date: new Date(Date.now() - 259200000).toISOString(),
        customer: "포스코",
        customerId: "c6",
        type: "payment",
        typeLabel: "지급",
        amount: 3500000,
        status: "completed",
        description: "외상 대금 지급",
        createdAt: new Date(Date.now() - 259200000).toISOString(),
        updatedAt: new Date(Date.now() - 259200000).toISOString(),
    },
    {
        id: "TX-2024007",
        date: new Date(Date.now() - 345600000).toISOString(),
        customer: "LG이노텍",
        customerId: "c7",
        type: "sales",
        typeLabel: "매출",
        amount: 2800000,
        status: "completed",
        description: "제어 패널 납품",
        createdAt: new Date(Date.now() - 345600000).toISOString(),
        updatedAt: new Date(Date.now() - 345600000).toISOString(),
    },
    {
        id: "TX-2024008",
        date: new Date(Date.now() - 432000000).toISOString(),
        customer: "한화솔루션",
        customerId: "c8",
        type: "purchase",
        typeLabel: "매입",
        amount: 1200000,
        status: "completed",
        description: "부품 구매",
        createdAt: new Date(Date.now() - 432000000).toISOString(),
        updatedAt: new Date(Date.now() - 432000000).toISOString(),
    },
];

// GET: 거래 목록 조회
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const type = searchParams.get("type");
        const status = searchParams.get("status");
        const customerId = searchParams.get("customerId");
        const startDate = searchParams.get("startDate");
        const endDate = searchParams.get("endDate");
        const limit = parseInt(searchParams.get("limit") || "10");
        const offset = parseInt(searchParams.get("offset") || "0");

        let filteredTransactions = [...transactions];

        // 타입 필터
        if (type) {
            filteredTransactions = filteredTransactions.filter(t => t.type === type);
        }

        // 상태 필터
        if (status) {
            filteredTransactions = filteredTransactions.filter(t => t.status === status);
        }

        // 거래처 필터
        if (customerId) {
            filteredTransactions = filteredTransactions.filter(t => t.customerId === customerId);
        }

        // 날짜 필터
        if (startDate) {
            const start = new Date(startDate);
            filteredTransactions = filteredTransactions.filter(t => new Date(t.date) >= start);
        }
        if (endDate) {
            const end = new Date(endDate);
            filteredTransactions = filteredTransactions.filter(t => new Date(t.date) <= end);
        }

        // 날짜 내림차순 정렬
        filteredTransactions.sort((a, b) =>
            new Date(b.date).getTime() - new Date(a.date).getTime()
        );

        // 통계 계산
        const stats = {
            totalSales: transactions.filter(t => t.type === "sales").reduce((sum, t) => sum + t.amount, 0),
            totalPurchases: transactions.filter(t => t.type === "purchase").reduce((sum, t) => sum + t.amount, 0),
            totalCollections: transactions.filter(t => t.type === "collection").reduce((sum, t) => sum + t.amount, 0),
            totalPayments: transactions.filter(t => t.type === "payment").reduce((sum, t) => sum + t.amount, 0),
            overdueAmount: transactions.filter(t => t.status === "overdue").reduce((sum, t) => sum + t.amount, 0),
            pendingCount: transactions.filter(t => t.status === "pending").length,
            overdueCount: transactions.filter(t => t.status === "overdue").length,
        };

        // 페이지네이션
        const total = filteredTransactions.length;
        const paginatedTransactions = filteredTransactions.slice(offset, offset + limit);

        return NextResponse.json({
            success: true,
            transactions: paginatedTransactions,
            stats,
            pagination: {
                total,
                limit,
                offset,
                hasMore: offset + limit < total,
            },
        });
    } catch (error) {
        console.error("Transactions GET error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to fetch transactions" },
            { status: 500 }
        );
    }
}

// POST: 새 거래 생성
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        // 입력 유효성 검증
        const validTypes = ["sales", "purchase", "collection", "payment"];
        if (!body.type || !validTypes.includes(body.type)) {
            return NextResponse.json(
                { success: false, error: `거래 유형(type)은 필수이며 ${validTypes.join(', ')} 중 하나여야 합니다`, code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        if (!body.customer || typeof body.customer !== "string" || body.customer.trim() === "") {
            return NextResponse.json(
                { success: false, error: "거래처명(customer)은 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        if (!body.customerId || typeof body.customerId !== "string") {
            return NextResponse.json(
                { success: false, error: "거래처 ID(customerId)는 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }
        if (body.amount === undefined || typeof body.amount !== "number" || body.amount <= 0) {
            return NextResponse.json(
                { success: false, error: "금액(amount)은 0보다 큰 숫자여야 합니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }

        const typeLabels = {
            sales: "매출",
            purchase: "매입",
            collection: "수금",
            payment: "지급",
        };

        const newTransaction: Transaction = {
            id: `TX-${Date.now().toString().slice(-7)}`,
            date: body.date || new Date().toISOString(),
            customer: body.customer.trim(),
            customerId: body.customerId,
            type: body.type,
            typeLabel: typeLabels[body.type as keyof typeof typeLabels] || body.type,
            amount: body.amount,
            status: body.status || "pending",
            description: body.description,
            items: body.items,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };

        transactions.unshift(newTransaction);

        return NextResponse.json({
            success: true,
            transaction: newTransaction,
        });
    } catch (error) {
        console.error("Transactions POST error:", error);
        return NextResponse.json(
            { success: false, error: "거래 생성에 실패했습니다", code: "E_INTERNAL" },
            { status: 500 }
        );
    }
}

// PUT: 거래 수정
export async function PUT(request: NextRequest) {
    try {
        const body = await request.json();
        const { id, ...updates } = body;

        const transactionIndex = transactions.findIndex(t => t.id === id);
        if (transactionIndex === -1) {
            return NextResponse.json(
                { success: false, error: "Transaction not found" },
                { status: 404 }
            );
        }

        transactions[transactionIndex] = {
            ...transactions[transactionIndex],
            ...updates,
            updatedAt: new Date().toISOString(),
        };

        return NextResponse.json({
            success: true,
            transaction: transactions[transactionIndex],
        });
    } catch (error) {
        console.error("Transactions PUT error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to update transaction" },
            { status: 500 }
        );
    }
}

// DELETE: 거래 삭제
export async function DELETE(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get("id");

        if (!id) {
            return NextResponse.json(
                { success: false, error: "Transaction ID required" },
                { status: 400 }
            );
        }

        const transactionIndex = transactions.findIndex(t => t.id === id);
        if (transactionIndex === -1) {
            return NextResponse.json(
                { success: false, error: "Transaction not found" },
                { status: 404 }
            );
        }

        transactions.splice(transactionIndex, 1);

        return NextResponse.json({
            success: true,
            message: "Transaction deleted",
        });
    } catch (error) {
        console.error("Transactions DELETE error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to delete transaction" },
            { status: 500 }
        );
    }
}
