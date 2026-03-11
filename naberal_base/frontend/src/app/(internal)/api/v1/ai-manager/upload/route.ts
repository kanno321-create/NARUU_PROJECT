import { NextRequest, NextResponse } from "next/server";

/**
 * AI Manager Upload API Route
 * 파일 업로드를 백엔드 FastAPI로 프록시
 */

// Railway URL을 기본값으로 사용 (데스크탑 앱 배포 대응)
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || "https://naberalproject-production.up.railway.app";

export async function POST(request: NextRequest) {
    try {
        // FormData 그대로 전달
        const formData = await request.formData();

        // 백엔드 AI Manager 업로드 API 호출
        const response = await fetch(`${BACKEND_URL}/v1/ai-manager/upload`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Backend upload error:", errorText);
            return NextResponse.json(
                {
                    error: "업로드 실패",
                    details: errorText,
                },
                { status: response.status }
            );
        }

        const data = await response.json();

        return NextResponse.json(data);
    } catch (error) {
        console.error("Upload route error:", error);
        return NextResponse.json(
            {
                error: `업로드 처리 중 오류가 발생했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
            },
            { status: 500 }
        );
    }
}
