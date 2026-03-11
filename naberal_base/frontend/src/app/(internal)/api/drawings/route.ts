import { NextRequest, NextResponse } from "next/server";

// 도면 타입
interface Drawing {
    id: string;
    name: string;
    projectName: string;
    projectId: string;
    fileType: 'pdf' | 'dwg' | 'dxf' | 'jpg' | 'png' | 'xlsx';
    fileSize: number;
    uploadedAt: string;
    updatedAt: string;
    version: number;
    status: 'pending' | 'analyzed' | 'approved' | 'rejected';
    starred: boolean;
    tags: string[];
    folder: string;
    analysisResult?: {
        panels: number;
        breakers: number;
        mainBreaker?: string;
        estimatedCost?: number;
    };
    sharedWith?: string[];
    uploadedBy: string;
    viewedAt?: string;
    versionHistory?: { version: number; date: string; uploadedBy: string }[];
}

// 메모리 스토리지 (서버 재시작 시 초기화됨)
let drawings: Drawing[] = [
    {
        id: '1',
        name: 'OO빌딩_분전반도면_v3.pdf',
        projectName: 'OO빌딩 신축공사',
        projectId: 'p1',
        fileType: 'pdf',
        fileSize: 2500000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        version: 3,
        status: 'analyzed',
        starred: true,
        tags: ['분전반', '신축', '상도'],
        folder: '진행중',
        analysisResult: {
            panels: 3,
            breakers: 24,
            mainBreaker: 'SBE-104 100A',
            estimatedCost: 4500000
        },
        sharedWith: ['park@vendor.kr', 'kim@partner.co.kr'],
        uploadedBy: '홍길동',
        viewedAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        versionHistory: [
            { version: 1, date: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(), uploadedBy: '홍길동' },
            { version: 2, date: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), uploadedBy: '홍길동' },
            { version: 3, date: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), uploadedBy: '홍길동' },
        ]
    },
    {
        id: '2',
        name: 'XX공장_배전반도면.dwg',
        projectName: 'XX공장 증설',
        projectId: 'p2',
        fileType: 'dwg',
        fileSize: 4500000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
        version: 2,
        status: 'analyzed',
        starred: false,
        tags: ['배전반', '공장', 'LS'],
        folder: '진행중',
        analysisResult: {
            panels: 5,
            breakers: 48,
            mainBreaker: 'SBE-403 300A',
            estimatedCost: 12500000
        },
        uploadedBy: '김철수',
        viewedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        versionHistory: [
            { version: 1, date: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), uploadedBy: '김철수' },
            { version: 2, date: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), uploadedBy: '김철수' },
        ]
    },
    {
        id: '3',
        name: '현장사진_전기실.jpg',
        projectName: 'YY아파트 리모델링',
        projectId: 'p3',
        fileType: 'jpg',
        fileSize: 1200000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
        version: 1,
        status: 'pending',
        starred: false,
        tags: ['현장사진', '리모델링'],
        folder: '진행중',
        uploadedBy: '이영희'
    },
    {
        id: '4',
        name: 'ZZ오피스_단선결선도.pdf',
        projectName: 'ZZ오피스 인테리어',
        projectId: 'p4',
        fileType: 'pdf',
        fileSize: 3200000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
        version: 1,
        status: 'approved',
        starred: true,
        tags: ['단선결선도', '오피스'],
        folder: '완료',
        analysisResult: {
            panels: 2,
            breakers: 16,
            mainBreaker: 'SBE-103 75A',
            estimatedCost: 2800000
        },
        uploadedBy: '홍길동',
        viewedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
    },
    {
        id: '5',
        name: 'AA센터_변전실배치도.dwg',
        projectName: 'AA센터 신축',
        projectId: 'p5',
        fileType: 'dwg',
        fileSize: 5800000,
        uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 96).toISOString(),
        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
        version: 4,
        status: 'analyzed',
        starred: false,
        tags: ['변전실', '배치도', '대형'],
        folder: '진행중',
        analysisResult: {
            panels: 8,
            breakers: 96,
            mainBreaker: 'SBE-603 500A',
            estimatedCost: 45000000
        },
        uploadedBy: '박지민',
        versionHistory: [
            { version: 1, date: new Date(Date.now() - 1000 * 60 * 60 * 120).toISOString(), uploadedBy: '박지민' },
            { version: 2, date: new Date(Date.now() - 1000 * 60 * 60 * 108).toISOString(), uploadedBy: '박지민' },
            { version: 3, date: new Date(Date.now() - 1000 * 60 * 60 * 84).toISOString(), uploadedBy: '박지민' },
            { version: 4, date: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(), uploadedBy: '박지민' },
        ]
    }
];

// GET: 도면 목록 조회
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const folder = searchParams.get("folder");
        const status = searchParams.get("status");
        const projectId = searchParams.get("projectId");
        const search = searchParams.get("search");
        const tags = searchParams.get("tags");

        let filteredDrawings = [...drawings];

        // 폴더 필터
        if (folder && folder !== '전체') {
            filteredDrawings = filteredDrawings.filter(d => d.folder === folder);
        }

        // 상태 필터
        if (status) {
            filteredDrawings = filteredDrawings.filter(d => d.status === status);
        }

        // 프로젝트 필터
        if (projectId) {
            filteredDrawings = filteredDrawings.filter(d => d.projectId === projectId);
        }

        // 검색 필터
        if (search) {
            const query = search.toLowerCase();
            filteredDrawings = filteredDrawings.filter(d =>
                d.name.toLowerCase().includes(query) ||
                d.projectName.toLowerCase().includes(query) ||
                d.tags.some(t => t.toLowerCase().includes(query))
            );
        }

        // 태그 필터
        if (tags) {
            const tagList = tags.split(",");
            filteredDrawings = filteredDrawings.filter(d =>
                tagList.some(tag => d.tags.includes(tag))
            );
        }

        // 통계 계산
        const stats = {
            total: drawings.length,
            analyzed: drawings.filter(d => d.status === 'analyzed').length,
            pending: drawings.filter(d => d.status === 'pending').length,
            approved: drawings.filter(d => d.status === 'approved').length,
            totalSize: drawings.reduce((acc, d) => acc + d.fileSize, 0)
        };

        return NextResponse.json({
            success: true,
            drawings: filteredDrawings,
            stats,
            total: filteredDrawings.length,
        });
    } catch (error) {
        console.error("Drawings GET error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to fetch drawings" },
            { status: 500 }
        );
    }
}

// POST: 새 도면 업로드 (메타데이터)
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        // 입력 유효성 검증
        if (!body.name || typeof body.name !== "string" || body.name.trim() === "") {
            return NextResponse.json(
                { success: false, error: "파일명(name)은 필수 항목입니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }

        // 허용된 파일 타입 검증
        const allowedTypes = ['pdf', 'dwg', 'dxf', 'jpg', 'png', 'xlsx'];
        if (body.fileType && !allowedTypes.includes(body.fileType)) {
            return NextResponse.json(
                { success: false, error: `허용되지 않는 파일 형식입니다. 허용: ${allowedTypes.join(', ')}`, code: "E_VALIDATION" },
                { status: 400 }
            );
        }

        // 파일 크기 검증 (100MB 제한)
        const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
        if (body.fileSize && body.fileSize > MAX_FILE_SIZE) {
            return NextResponse.json(
                { success: false, error: "파일 크기가 100MB를 초과할 수 없습니다", code: "E_VALIDATION" },
                { status: 400 }
            );
        }

        const newDrawing: Drawing = {
            id: `drawing-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
            name: body.name.trim(),
            projectName: body.projectName || '미지정',
            projectId: body.projectId || 'unassigned',
            fileType: body.fileType || 'pdf',
            fileSize: body.fileSize || 0,
            uploadedAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            version: 1,
            status: 'pending',
            starred: false,
            tags: Array.isArray(body.tags) ? body.tags : [],
            folder: body.folder || '진행중',
            uploadedBy: body.uploadedBy || '시스템',
            versionHistory: [
                { version: 1, date: new Date().toISOString(), uploadedBy: body.uploadedBy || '시스템' }
            ]
        };

        drawings.push(newDrawing);

        return NextResponse.json({
            success: true,
            drawing: newDrawing,
        });
    } catch (error) {
        console.error("Drawings POST error:", error);
        return NextResponse.json(
            { success: false, error: "도면 생성에 실패했습니다", code: "E_INTERNAL" },
            { status: 500 }
        );
    }
}

// PUT: 도면 수정
export async function PUT(request: NextRequest) {
    try {
        const body = await request.json();
        const { id, ...updates } = body;

        const drawingIndex = drawings.findIndex(d => d.id === id);
        if (drawingIndex === -1) {
            return NextResponse.json(
                { success: false, error: "Drawing not found" },
                { status: 404 }
            );
        }

        // 버전 업데이트인 경우
        if (updates.newVersion) {
            const currentDrawing = drawings[drawingIndex];
            const newVersion = currentDrawing.version + 1;
            updates.version = newVersion;
            updates.versionHistory = [
                ...(currentDrawing.versionHistory || []),
                { version: newVersion, date: new Date().toISOString(), uploadedBy: updates.uploadedBy || currentDrawing.uploadedBy }
            ];
        }

        // viewedAt 업데이트
        if (updates.viewed) {
            updates.viewedAt = new Date().toISOString();
            delete updates.viewed;
        }

        drawings[drawingIndex] = {
            ...drawings[drawingIndex],
            ...updates,
            updatedAt: new Date().toISOString()
        };

        return NextResponse.json({
            success: true,
            drawing: drawings[drawingIndex],
        });
    } catch (error) {
        console.error("Drawings PUT error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to update drawing" },
            { status: 500 }
        );
    }
}

// DELETE: 도면 삭제
export async function DELETE(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const ids = searchParams.get("ids");

        if (!ids) {
            return NextResponse.json(
                { success: false, error: "Drawing IDs required" },
                { status: 400 }
            );
        }

        const idList = ids.split(",");
        const deletedCount = idList.length;

        drawings = drawings.filter(d => !idList.includes(d.id));

        return NextResponse.json({
            success: true,
            deletedCount,
            message: `${deletedCount} drawing(s) deleted`,
        });
    } catch (error) {
        console.error("Drawings DELETE error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to delete drawings" },
            { status: 500 }
        );
    }
}
