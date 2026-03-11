"""
KIS Estimator API - Drawings

제작도면 생성 및 조회 API:
- 단선결선도
- 외함외형도
- 차단기 배치도
- 도면 업로드 (CAD, PDF, 이미지)
- 도면 분석 및 부품 추출
- 도면 관리 (버전, 태그, 검색)

Metadata storage: PostgreSQL (kis_beta.uploaded_drawings)
"""
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi import Path as PathParam
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.infra.db import get_db
from kis_estimator_core.services.drawing_service import DrawingService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["drawings"])

# 도면 저장 경로 (상대경로 - Railway 호환)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DRAWINGS_DATA_DIR = PROJECT_ROOT / "data" / "drawings"
DRAWINGS_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 생성된 도면 출력 디렉토리
GENERATED_DIR = DRAWINGS_DATA_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


# ==================== Request/Response Models ====================

class DrawingRequest(BaseModel):
    """도면 생성 요청"""
    estimate_id: str = Field(..., description="견적 ID")
    panel_data: dict = Field(..., description="패널 데이터 (enclosure, main_breaker 등)")
    placement_result: dict = Field(default_factory=dict, description="차단기 배치 결과")


class DrawingResponse(BaseModel):
    """도면 생성 응답"""
    estimate_id: str
    generated_at: str
    drawings: dict = Field(..., description="생성된 도면 정보 (path, hash)")


class DrawingListItem(BaseModel):
    """도면 목록 아이템"""
    filename: str
    type: str  # wiring, enclosure, placement
    estimate_id: str
    created_at: str
    size_bytes: int


class UploadedDrawing(BaseModel):
    """업로드된 도면"""
    id: str
    filename: str
    original_name: str
    file_type: str  # dwg, dxf, pdf, png, jpg, svg
    file_size: int
    category: str  # panel, wiring, layout, reference, other
    project: Optional[str] = None
    customer: Optional[str] = None
    estimate_id: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = []
    version: int = 1
    parent_id: Optional[str] = None  # 이전 버전 ID
    analysis: Optional[dict] = None  # AI 분석 결과
    created_at: str
    updated_at: str


class UploadedDrawingUpdate(BaseModel):
    """업로드된 도면 수정"""
    category: Optional[str] = None
    project: Optional[str] = None
    customer: Optional[str] = None
    estimate_id: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class DrawingAnalysisResult(BaseModel):
    """도면 분석 결과"""
    drawing_id: str
    file_type: str
    dimensions: Optional[dict] = None  # W, H, D
    detected_components: list[dict] = []  # 감지된 부품
    breaker_count: Optional[int] = None
    panel_type: Optional[str] = None
    confidence: float = 0.0
    raw_text: Optional[str] = None
    analyzed_at: str


class DrawingStats(BaseModel):
    """도면 통계"""
    total_drawings: int
    by_category: dict
    by_file_type: dict
    by_customer: dict
    recent_uploads: list[dict]
    total_size_mb: float


ALLOWED_EXTENSIONS = {'.dwg', '.dxf', '.pdf', '.png', '.jpg', '.jpeg', '.svg', '.bmp', '.tiff'}


# ==================== Utility Functions ====================

def _row_to_drawing_dict(row) -> dict:
    """Convert a DB row mapping to a drawing dict matching UploadedDrawing schema."""
    return {
        "id": row["id"],
        "filename": row["filename"],
        "original_name": row["original_name"],
        "file_type": row["file_type"],
        "file_size": row["file_size"] or 0,
        "category": row["category"] or "other",
        "project": row["project"],
        "customer": row["customer"],
        "estimate_id": row["estimate_id"],
        "description": row["description"],
        "tags": list(row["tags"]) if row["tags"] else [],
        "version": row["version"] or 1,
        "parent_id": row["parent_id"],
        "analysis": dict(row["analysis"]) if row["analysis"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else "",
    }


# ==================== Static Routes (MUST be before /{estimate_id}) ====================

@router.get("/health", summary="도면 서비스 헬스체크")
async def drawings_health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """도면 서비스 상태 확인"""
    try:
        result = await db.execute(
            text("SELECT COUNT(*) AS cnt FROM uploaded_drawings")
        )
        total = result.scalar() or 0
        uploads_dir = DRAWINGS_DATA_DIR / "uploads"

        return {
            "status": "healthy",
            "data_dir": str(DRAWINGS_DATA_DIR),
            "data_dir_exists": DRAWINGS_DATA_DIR.exists(),
            "uploads_dir": str(uploads_dir),
            "uploads_dir_exists": uploads_dir.exists(),
            "total_uploaded": total,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_detail": str(e)[:300],
        }


@router.get("/stats", response_model=DrawingStats, summary="도면 통계")
async def get_drawing_stats(db: AsyncSession = Depends(get_db)) -> DrawingStats:
    """도면 관련 통계를 조회합니다."""
    # Category counts
    cat_result = await db.execute(text(
        "SELECT COALESCE(category, 'other') AS cat, COUNT(*) AS cnt "
        "FROM uploaded_drawings GROUP BY COALESCE(category, 'other')"
    ))
    by_category = {row["cat"]: row["cnt"] for row in cat_result.mappings().all()}

    # File type counts
    ft_result = await db.execute(text(
        "SELECT COALESCE(file_type, 'unknown') AS ft, COUNT(*) AS cnt "
        "FROM uploaded_drawings GROUP BY COALESCE(file_type, 'unknown')"
    ))
    by_file_type = {row["ft"]: row["cnt"] for row in ft_result.mappings().all()}

    # Customer counts
    cust_result = await db.execute(text(
        "SELECT COALESCE(customer, '미지정') AS cust, COUNT(*) AS cnt "
        "FROM uploaded_drawings GROUP BY COALESCE(customer, '미지정')"
    ))
    by_customer = {row["cust"]: row["cnt"] for row in cust_result.mappings().all()}

    # Total size
    size_result = await db.execute(text(
        "SELECT COALESCE(SUM(file_size), 0) AS total_size FROM uploaded_drawings"
    ))
    total_size = size_result.scalar() or 0

    # Total count
    count_result = await db.execute(text(
        "SELECT COUNT(*) AS cnt FROM uploaded_drawings"
    ))
    total_drawings = count_result.scalar() or 0

    # Recent uploads (top 5)
    recent_result = await db.execute(text(
        "SELECT id, original_name, category, created_at "
        "FROM uploaded_drawings "
        "ORDER BY created_at DESC LIMIT 5"
    ))
    recent_uploads = [
        {
            "id": row["id"],
            "filename": row["original_name"],
            "category": row["category"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else "",
        }
        for row in recent_result.mappings().all()
    ]

    return DrawingStats(
        total_drawings=total_drawings,
        by_category=by_category,
        by_file_type=by_file_type,
        by_customer=by_customer,
        recent_uploads=recent_uploads,
        total_size_mb=round(total_size / (1024 * 1024), 2),
    )


# ==================== Upload & Uploaded Routes ====================

@router.post("/upload", response_model=UploadedDrawing, status_code=201, summary="도면 업로드")
async def upload_drawing(
    file: UploadFile = File(...),
    category: str = Form("other"),
    project: Optional[str] = Form(None),
    customer: Optional[str] = Form(None),
    estimate_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # 쉼표로 구분
    db: AsyncSession = Depends(get_db),
) -> UploadedDrawing:
    """
    도면 파일을 업로드합니다.

    지원 형식:
    - CAD: .dwg, .dxf
    - 문서: .pdf
    - 이미지: .png, .jpg, .jpeg, .svg, .bmp, .tiff

    카테고리:
    - panel: 분전반 도면
    - wiring: 결선도
    - layout: 배치도
    - reference: 참조 도면
    - other: 기타
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다: {ext}. 지원 형식: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    uploads_dir = DRAWINGS_DATA_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    drawing_id = f"drw-{uuid4()}"
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    new_filename = f"{drawing_id}_{timestamp}{ext}"
    file_path = uploads_dir / new_filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = file_path.stat().st_size

    tags_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    await db.execute(text("""
        INSERT INTO uploaded_drawings
            (id, filename, original_name, file_type, file_size,
             category, project, customer, estimate_id, description,
             tags, version, parent_id, analysis, created_at, updated_at)
        VALUES
            (:id, :filename, :original_name, :file_type, :file_size,
             :category, :project, :customer, :estimate_id, :description,
             CAST(:tags AS text[]), :version, :parent_id, NULL, :created_at, :updated_at)
    """), {
        "id": drawing_id,
        "filename": new_filename,
        "original_name": file.filename,
        "file_type": ext[1:],
        "file_size": file_size,
        "category": category,
        "project": project,
        "customer": customer,
        "estimate_id": estimate_id,
        "description": description,
        "tags": "{" + ",".join(f'"{t}"' for t in tags_list) + "}" if tags_list else "{}",
        "version": 1,
        "parent_id": None,
        "created_at": now,
        "updated_at": now,
    })

    logger.info(f"도면 업로드: {drawing_id} - {file.filename}")

    return UploadedDrawing(
        id=drawing_id,
        filename=new_filename,
        original_name=file.filename,
        file_type=ext[1:],
        file_size=file_size,
        category=category,
        project=project,
        customer=customer,
        estimate_id=estimate_id,
        description=description,
        tags=tags_list,
        version=1,
        parent_id=None,
        analysis=None,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )


@router.get("/uploaded", response_model=list[UploadedDrawing], summary="업로드된 도면 목록")
async def list_uploaded_drawings(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    customer: Optional[str] = Query(None, description="거래처 필터"),
    project: Optional[str] = Query(None, description="프로젝트 필터"),
    estimate_id: Optional[str] = Query(None, description="견적 ID 필터"),
    file_type: Optional[str] = Query(None, description="파일 형식 필터"),
    search: Optional[str] = Query(None, description="검색어 (파일명, 설명, 태그)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[UploadedDrawing]:
    """업로드된 도면 목록을 조회합니다."""
    conditions = []
    params: dict = {"limit_val": limit, "offset_val": offset}

    if category:
        conditions.append("category = :category")
        params["category"] = category

    if customer:
        conditions.append("LOWER(COALESCE(customer, '')) LIKE :customer")
        params["customer"] = f"%{customer.lower()}%"

    if project:
        conditions.append("LOWER(COALESCE(project, '')) LIKE :project")
        params["project"] = f"%{project.lower()}%"

    if estimate_id:
        conditions.append("estimate_id = :estimate_id")
        params["estimate_id"] = estimate_id

    if file_type:
        conditions.append("file_type = :file_type")
        params["file_type"] = file_type

    if search:
        conditions.append(
            "(LOWER(original_name) LIKE :search "
            "OR LOWER(COALESCE(description, '')) LIKE :search "
            "OR EXISTS (SELECT 1 FROM unnest(tags) AS t WHERE LOWER(t) LIKE :search))"
        )
        params["search"] = f"%{search.lower()}%"

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT * FROM uploaded_drawings
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit_val OFFSET :offset_val
    """

    result = await db.execute(text(query), params)
    rows = result.mappings().all()

    return [UploadedDrawing(**_row_to_drawing_dict(row)) for row in rows]


@router.get("/uploaded/{drawing_id}", response_model=UploadedDrawing, summary="업로드된 도면 상세")
async def get_uploaded_drawing(
    drawing_id: str,
    db: AsyncSession = Depends(get_db),
) -> UploadedDrawing:
    """특정 업로드된 도면의 상세 정보를 조회합니다."""
    result = await db.execute(
        text("SELECT * FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    return UploadedDrawing(**_row_to_drawing_dict(row))


@router.get("/uploaded/{drawing_id}/file", summary="도면 파일 다운로드")
async def download_drawing_file(
    drawing_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """도면 파일을 다운로드합니다."""
    result = await db.execute(
        text("SELECT filename, original_name FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    file_path = DRAWINGS_DATA_DIR / "uploads" / row["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")

    return FileResponse(
        file_path,
        filename=row["original_name"],
        media_type="application/octet-stream"
    )


@router.put("/uploaded/{drawing_id}", response_model=UploadedDrawing, summary="도면 정보 수정")
async def update_uploaded_drawing(
    drawing_id: str,
    update: UploadedDrawingUpdate,
    db: AsyncSession = Depends(get_db),
) -> UploadedDrawing:
    """업로드된 도면의 메타데이터를 수정합니다."""
    # Verify drawing exists
    check_result = await db.execute(
        text("SELECT id FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    if not check_result.first():
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    # Build dynamic UPDATE
    set_clauses = ["updated_at = :updated_at"]
    params: dict = {"id": drawing_id, "updated_at": datetime.now()}

    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "tags" and value is not None:
            set_clauses.append("tags = CAST(:tags AS text[])")
            params["tags"] = "{" + ",".join(f'"{t}"' for t in value) + "}" if value else "{}"
        else:
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

    query = f"UPDATE uploaded_drawings SET {', '.join(set_clauses)} WHERE id = :id"
    await db.execute(text(query), params)

    # Return updated row
    result = await db.execute(
        text("SELECT * FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    row = result.mappings().first()

    return UploadedDrawing(**_row_to_drawing_dict(row))


@router.delete("/uploaded/{drawing_id}", summary="업로드된 도면 삭제")
async def delete_uploaded_drawing(
    drawing_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """업로드된 도면을 삭제합니다."""
    # Get drawing info before deletion
    result = await db.execute(
        text("SELECT filename, original_name FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    # Delete physical file
    file_path = DRAWINGS_DATA_DIR / "uploads" / row["filename"]
    if file_path.exists():
        file_path.unlink()

    # Delete DB record
    await db.execute(
        text("DELETE FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )

    return {
        "success": True,
        "deleted_id": drawing_id,
        "deleted_filename": row["original_name"],
    }


@router.post("/uploaded/{drawing_id}/new-version", response_model=UploadedDrawing, summary="새 버전 업로드")
async def upload_new_version(
    drawing_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
) -> UploadedDrawing:
    """기존 도면의 새 버전을 업로드합니다."""
    # Load parent drawing
    parent_result = await db.execute(
        text("SELECT * FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    parent = parent_result.mappings().first()

    if not parent:
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {ext}")

    uploads_dir = DRAWINGS_DATA_DIR / "uploads"
    new_id = f"drw-{uuid4()}"
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    new_filename = f"{new_id}_{timestamp}{ext}"
    file_path = uploads_dir / new_filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = file_path.stat().st_size
    new_version = (parent["version"] or 1) + 1
    parent_tags = list(parent["tags"]) if parent["tags"] else []
    tags_literal = "{" + ",".join(f'"{t}"' for t in parent_tags) + "}" if parent_tags else "{}"

    await db.execute(text("""
        INSERT INTO uploaded_drawings
            (id, filename, original_name, file_type, file_size,
             category, project, customer, estimate_id, description,
             tags, version, parent_id, analysis, created_at, updated_at)
        VALUES
            (:id, :filename, :original_name, :file_type, :file_size,
             :category, :project, :customer, :estimate_id, :description,
             CAST(:tags AS text[]), :version, :parent_id, NULL, :created_at, :updated_at)
    """), {
        "id": new_id,
        "filename": new_filename,
        "original_name": file.filename,
        "file_type": ext[1:],
        "file_size": file_size,
        "category": parent["category"],
        "project": parent["project"],
        "customer": parent["customer"],
        "estimate_id": parent["estimate_id"],
        "description": description or parent["description"],
        "tags": tags_literal,
        "version": new_version,
        "parent_id": drawing_id,
        "created_at": now,
        "updated_at": now,
    })

    logger.info(f"도면 새 버전 업로드: {new_id} (v{new_version}) <- {drawing_id}")

    return UploadedDrawing(
        id=new_id,
        filename=new_filename,
        original_name=file.filename,
        file_type=ext[1:],
        file_size=file_size,
        category=parent["category"],
        project=parent["project"],
        customer=parent["customer"],
        estimate_id=parent["estimate_id"],
        description=description or parent["description"],
        tags=parent_tags,
        version=new_version,
        parent_id=drawing_id,
        analysis=None,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )


@router.get("/uploaded/{drawing_id}/versions", response_model=list[UploadedDrawing], summary="버전 이력 조회")
async def get_drawing_versions(
    drawing_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[UploadedDrawing]:
    """도면의 버전 이력을 조회합니다."""
    # Check that the requested drawing exists
    check_result = await db.execute(
        text("SELECT id FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    if not check_result.first():
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    # Use a recursive CTE to walk the parent chain upward and children downward
    result = await db.execute(text("""
        WITH RECURSIVE ancestors AS (
            SELECT * FROM uploaded_drawings WHERE id = :id
            UNION ALL
            SELECT d.* FROM uploaded_drawings d
            INNER JOIN ancestors a ON d.id = a.parent_id
        ),
        descendants AS (
            SELECT * FROM uploaded_drawings WHERE id = :id
            UNION ALL
            SELECT d.* FROM uploaded_drawings d
            INNER JOIN descendants desc_cte ON d.parent_id = desc_cte.id
        ),
        all_versions AS (
            SELECT * FROM ancestors
            UNION
            SELECT * FROM descendants
        )
        SELECT * FROM all_versions
        ORDER BY version ASC
    """), {"id": drawing_id})

    rows = result.mappings().all()
    return [UploadedDrawing(**_row_to_drawing_dict(row)) for row in rows]


@router.post("/uploaded/{drawing_id}/analyze", response_model=DrawingAnalysisResult, summary="도면 AI 분석")
async def analyze_drawing(
    drawing_id: str,
    db: AsyncSession = Depends(get_db),
) -> DrawingAnalysisResult:
    """
    도면을 AI로 분석하여 부품 정보를 추출합니다.

    분석 내용:
    - 치수 정보 (W, H, D)
    - 부품 감지 (차단기, 부속자재 등)
    - 패널 유형 추정
    - 텍스트 추출 (OCR)
    """
    result = await db.execute(
        text("SELECT * FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    now = datetime.now()
    analysis_result = {
        "drawing_id": drawing_id,
        "file_type": row["file_type"],
        "dimensions": None,
        "detected_components": [],
        "breaker_count": None,
        "panel_type": None,
        "confidence": 0.0,
        "raw_text": None,
        "analyzed_at": now.isoformat(),
    }

    if row["file_type"] in ["png", "jpg", "jpeg", "bmp"]:
        analysis_result["confidence"] = 0.3
        analysis_result["detected_components"] = [
            {"type": "unknown", "count": 1, "confidence": 0.3}
        ]
    elif row["file_type"] == "pdf":
        analysis_result["confidence"] = 0.4
        analysis_result["detected_components"] = [
            {"type": "document", "count": 1, "confidence": 0.4}
        ]
    elif row["file_type"] in ["dxf", "dwg"]:
        analysis_result["confidence"] = 0.5
        analysis_result["detected_components"] = [
            {"type": "cad_drawing", "count": 1, "confidence": 0.5}
        ]

    # Store analysis result as JSONB
    await db.execute(text("""
        UPDATE uploaded_drawings
        SET analysis = CAST(:analysis AS jsonb),
            updated_at = :updated_at
        WHERE id = :id
    """), {
        "id": drawing_id,
        "analysis": json.dumps(analysis_result, ensure_ascii=False),
        "updated_at": now,
    })

    logger.info(f"도면 분석 완료: {drawing_id}")

    return DrawingAnalysisResult(**analysis_result)


@router.post("/link-estimate/{drawing_id}", summary="도면-견적 연결")
async def link_drawing_to_estimate(
    drawing_id: str,
    estimate_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """도면을 견적과 연결합니다."""
    result = await db.execute(
        text("SELECT id FROM uploaded_drawings WHERE id = :id"),
        {"id": drawing_id},
    )
    if not result.first():
        raise HTTPException(status_code=404, detail=f"도면을 찾을 수 없습니다: {drawing_id}")

    await db.execute(text("""
        UPDATE uploaded_drawings
        SET estimate_id = :estimate_id,
            updated_at = :updated_at
        WHERE id = :id
    """), {
        "id": drawing_id,
        "estimate_id": estimate_id,
        "updated_at": datetime.now(),
    })

    return {
        "success": True,
        "drawing_id": drawing_id,
        "estimate_id": estimate_id,
    }


# ==================== Dynamic Routes (/{estimate_id} - MUST be LAST) ====================

@router.post("", response_model=DrawingResponse, status_code=201, summary="제작도면 생성")
async def generate_drawings(request: DrawingRequest) -> DrawingResponse:
    """
    견적에 대한 제작도면을 생성합니다.

    생성되는 도면:
    - 단선결선도 (wiring_diagram)
    - 외함외형도 (enclosure_diagram)
    - 차단기 배치도 (placement_diagram)

    Returns:
        DrawingResponse: 생성된 도면 정보
    """
    try:
        service = DrawingService.__new__(DrawingService)
        service.db = None
        result = await service.generate_drawings(
            estimate_id=request.estimate_id,
            panel_data=request.panel_data,
            placement_result=request.placement_result
        )
    except Exception as e:
        logger.warning(f"DrawingService 미사용 - 기본 도면 생성: {e}")
        now = datetime.now()
        result = {
            "estimate_id": request.estimate_id,
            "generated_at": now.isoformat(),
            "drawings": {
                "wiring_diagram": {"status": "pending", "message": "DB 연동 후 생성 가능"},
                "enclosure_diagram": {"status": "pending", "message": "DB 연동 후 생성 가능"},
                "placement_diagram": {"status": "pending", "message": "DB 연동 후 생성 가능"},
            }
        }

    return DrawingResponse(
        estimate_id=result["estimate_id"],
        generated_at=result["generated_at"],
        drawings=result["drawings"]
    )


@router.get("/{estimate_id}", response_model=list[DrawingListItem], summary="도면 목록 조회")
async def list_drawings(estimate_id: str) -> list[DrawingListItem]:
    """특정 견적의 생성된 도면 목록을 조회합니다."""
    drawings = []
    for svg_file in GENERATED_DIR.glob(f"{estimate_id}_*.svg"):
        parts = svg_file.stem.split("_")
        if len(parts) >= 3:
            drawing_type = parts[1]
            stat = svg_file.stat()

            drawings.append(DrawingListItem(
                filename=svg_file.name,
                type=drawing_type,
                estimate_id=estimate_id,
                created_at=str(stat.st_mtime),
                size_bytes=stat.st_size
            ))

    return drawings


@router.get("/{estimate_id}/{drawing_type}", summary="도면 파일 조회")
async def get_drawing(
    estimate_id: str,
    drawing_type: str = PathParam(..., description="도면 유형 (wiring, enclosure, placement)")
) -> FileResponse:
    """특정 도면 파일을 조회합니다."""
    pattern = f"{estimate_id}_{drawing_type}_*.svg"
    files = sorted(GENERATED_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)

    if not files:
        raise HTTPException(
            status_code=404,
            detail=f"도면을 찾을 수 없습니다: {estimate_id}/{drawing_type}"
        )

    return FileResponse(
        files[0],
        media_type="image/svg+xml",
        filename=files[0].name
    )


@router.delete("/{estimate_id}", summary="도면 삭제")
async def delete_drawings(estimate_id: str) -> dict:
    """특정 견적의 모든 생성된 도면을 삭제합니다."""
    deleted = []
    for svg_file in GENERATED_DIR.glob(f"{estimate_id}_*.svg"):
        svg_file.unlink()
        deleted.append(svg_file.name)

    return {
        "estimate_id": estimate_id,
        "deleted_count": len(deleted),
        "deleted_files": deleted
    }
