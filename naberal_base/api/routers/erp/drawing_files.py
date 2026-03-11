"""
KIS ERP - 도면 파일 관리 API
도면 파일 업로드/다운로드/목록/수정/삭제 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from kis_erp_core.services.drawing_file_service import DrawingFileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drawing-files", tags=["ERP - 도면파일"])

ALLOWED_TYPES = {"pdf", "dwg", "dxf", "jpg", "jpeg", "png", "svg", "xlsx", "bmp", "tiff"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


class DrawingFileResponse(BaseModel):
    id: str
    drawing_name: str
    file_name: str
    file_type: str
    file_size: int
    project_name: Optional[str] = None
    customer_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    version: int = 1
    status: str = "uploaded"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DrawingFileUpdate(BaseModel):
    drawing_name: Optional[str] = None
    project_name: Optional[str] = None
    customer_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


def _to_response(r: dict) -> DrawingFileResponse:
    return DrawingFileResponse(
        id=r["id"],
        drawing_name=r["drawing_name"],
        file_name=r["file_name"],
        file_type=r["file_type"],
        file_size=r["file_size"],
        project_name=r.get("project_name"),
        customer_name=r.get("customer_name"),
        description=r.get("description"),
        tags=r.get("tags", []),
        version=r.get("version", 1),
        status=r.get("status", "uploaded"),
        created_at=str(r["created_at"]) if r.get("created_at") else None,
        updated_at=str(r["updated_at"]) if r.get("updated_at") else None,
    )


@router.post("", response_model=DrawingFileResponse, status_code=201, summary="도면 파일 업로드")
async def upload_drawing_file(
    file: UploadFile = File(..., description="도면 파일"),
    drawing_name: str = Form(..., description="도면명"),
    project_name: Optional[str] = Form(None, description="프로젝트명"),
    customer_name: Optional[str] = Form(None, description="고객명"),
    description: Optional[str] = Form(None, description="설명"),
    tags: Optional[str] = Form(None, description="태그 (쉼표 구분)"),
    db: AsyncSession = Depends(get_db),
) -> DrawingFileResponse:
    """도면 파일을 데이터베이스에 저장합니다."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"허용되지 않는 파일 형식입니다: {ext}")

    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 100MB를 초과합니다")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    service = DrawingFileService()
    try:
        await service.ensure_table(db)
    except Exception:
        logger.warning("Table ensure_table failed (may already exist)")

    result = await service.save_file(
        db, drawing_name, file.filename, ext, file_data,
        project_name, customer_name, description, tag_list,
    )
    await db.commit()

    return _to_response(result)


@router.get("", response_model=List[DrawingFileResponse], summary="도면 파일 목록 조회")
async def list_drawing_files(
    search: Optional[str] = Query(None, description="도면명/파일명/고객명 검색"),
    project_name: Optional[str] = Query(None, description="프로젝트명 필터"),
    status: Optional[str] = Query(None, description="상태 필터"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[DrawingFileResponse]:
    """저장된 도면 파일 목록을 조회합니다."""
    service = DrawingFileService()
    try:
        await service.ensure_table(db)
    except Exception:
        pass

    results = await service.list_files(db, search, project_name, status, skip, limit)
    return [_to_response(r) for r in results]


@router.get("/{file_id}", response_model=DrawingFileResponse, summary="도면 파일 상세 조회")
async def get_drawing_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> DrawingFileResponse:
    """도면 파일 메타데이터를 조회합니다."""
    service = DrawingFileService()
    result = await service.get_file(db, file_id)
    if not result:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return _to_response(result)


@router.get("/{file_id}/download", summary="도면 파일 다운로드")
async def download_drawing_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """도면 파일을 다운로드합니다."""
    service = DrawingFileService()
    result = await service.get_file_data(db, file_id)
    if not result:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    return Response(
        content=bytes(result["file_data"]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{result["file_name"]}"',
            "Content-Length": str(result["file_size"]),
        },
    )


@router.put("/{file_id}", response_model=DrawingFileResponse, summary="도면 메타데이터 수정")
async def update_drawing_file(
    file_id: str,
    update: DrawingFileUpdate,
    db: AsyncSession = Depends(get_db),
) -> DrawingFileResponse:
    """도면 파일의 메타데이터를 수정합니다."""
    service = DrawingFileService()
    data = update.model_dump(exclude_unset=True)
    result = await service.update_file(db, file_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    await db.commit()
    return _to_response(result)


@router.delete("/{file_id}", status_code=204, summary="도면 파일 삭제")
async def delete_drawing_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """도면 파일을 삭제합니다."""
    service = DrawingFileService()
    success = await service.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    await db.commit()
