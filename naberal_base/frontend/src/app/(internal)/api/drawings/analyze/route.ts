import { NextRequest, NextResponse } from "next/server";

// AI 분석 시뮬레이션 API
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { drawingId, fileType, fileName } = body;

        if (!drawingId) {
            return NextResponse.json(
                { success: false, error: "Drawing ID required" },
                { status: 400 }
            );
        }

        // 분석 시뮬레이션 (실제 환경에서는 AI 모델 호출)
        // 파일 타입과 이름에 따라 다른 결과 생성
        const isPDF = fileType === 'pdf';
        const isDWG = fileType === 'dwg' || fileType === 'dxf';
        const isImage = ['jpg', 'jpeg', 'png'].includes(fileType?.toLowerCase());

        // 기본 분석 결과
        const baseResult = {
            panels: Math.floor(Math.random() * 5) + 1,
            breakers: Math.floor(Math.random() * 30) + 10,
            mainBreaker: getRandomMainBreaker(),
            estimatedCost: Math.floor(Math.random() * 10000000) + 1000000
        };

        // 파일 타입별 보정
        if (isDWG) {
            // DWG 파일은 더 상세한 분석 가능
            baseResult.panels = Math.floor(Math.random() * 8) + 2;
            baseResult.breakers = Math.floor(Math.random() * 50) + 20;
        } else if (isImage) {
            // 이미지는 제한적인 분석
            baseResult.panels = Math.floor(Math.random() * 3) + 1;
            baseResult.breakers = Math.floor(Math.random() * 15) + 5;
        }

        // 분석 신뢰도
        const confidence = isPDF ? 0.92 : isDWG ? 0.95 : 0.78;

        // 분석 상세 정보
        const analysisDetails = {
            fileAnalyzed: fileName || 'unknown',
            analysisTime: `${(Math.random() * 2 + 0.5).toFixed(1)}초`,
            confidence: confidence,
            detectedComponents: [
                { type: '메인차단기', count: 1 },
                { type: '분기차단기', count: baseResult.breakers },
                { type: '분전반', count: baseResult.panels },
                { type: '부스바', count: baseResult.panels },
            ],
            recommendations: getRecommendations(baseResult),
        };

        return NextResponse.json({
            success: true,
            drawingId,
            analysisResult: baseResult,
            analysisDetails,
            message: "AI 분석이 완료되었습니다.",
        });
    } catch (error) {
        console.error("Drawing analysis error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to analyze drawing" },
            { status: 500 }
        );
    }
}

function getRandomMainBreaker(): string {
    const breakers = [
        'SBE-103 75A',
        'SBE-104 100A',
        'SBE-203 150A',
        'SBE-204 200A',
        'SBE-403 300A',
        'SBE-404 400A',
        'SBE-603 500A',
    ];
    return breakers[Math.floor(Math.random() * breakers.length)];
}

function getRecommendations(result: { panels: number; breakers: number; estimatedCost: number }): string[] {
    const recommendations: string[] = [];

    if (result.breakers > 30) {
        recommendations.push('대용량 분전반 설계 권장');
    }
    if (result.panels > 3) {
        recommendations.push('다중 분전반 연결 검토 필요');
    }
    if (result.estimatedCost > 5000000) {
        recommendations.push('경제형 차단기 적용으로 비용 절감 가능');
    }

    if (recommendations.length === 0) {
        recommendations.push('표준 설계 적용 권장');
    }

    return recommendations;
}
