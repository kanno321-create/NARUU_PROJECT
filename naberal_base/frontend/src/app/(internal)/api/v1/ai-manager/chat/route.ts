import { NextRequest, NextResponse } from "next/server";

/**
 * AI Manager Chat API Route
 * 프론트엔드 요청을 백엔드 FastAPI로 프록시
 */

// Railway URL을 기본값으로 사용 (데스크탑 앱 배포 대응)
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || "https://naberalproject-production.up.railway.app";

export async function POST(request: NextRequest) {

    try {
        const body = await request.json();

        if (!body.message || typeof body.message !== "string" || body.message.length > 10000) {
            return NextResponse.json(
                { message: "유효하지 않은 메시지입니다." },
                { status: 400 }
            );
        }
        // 백엔드 AI Manager 채팅 API 호출 (시각화 지원)
        const response = await fetch(`${BACKEND_URL}/v1/ai-manager/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message: body.message,
                attachments: body.attachments || [],
                context: body.context || { recentMessages: [], currentVisualization: null },
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Backend error:", errorText);
            return NextResponse.json(
                {
                    message: "백엔드 응답 오류가 발생했습니다.",
                    error: errorText
                },
                { status: response.status }
            );
        }

        const data = await response.json();

        // AI Manager 응답 형식 그대로 전달
        return NextResponse.json({
            message: data.message || "응답을 받지 못했습니다.",
            visualizations: data.visualizations || [],
            command: data.command || null,
            suggestions: data.suggestions || [],
            timestamp: data.timestamp,
        });
    } catch (error) {
        console.error("API Route error:", error);
        return NextResponse.json(
            {
                message: `요청 처리 중 오류가 발생했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
                error: String(error)
            },
            { status: 500 }
        );
    }
}
