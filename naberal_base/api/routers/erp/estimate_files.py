"""
KIS ERP - 견적 파일 관리 API
견적 Excel/PDF 파일 업로드/다운로드/목록 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from kis_erp_core.services.estimate_file_service import EstimateFileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/estimate-files", tags=["ERP - 견적파일"])

ALLOWED_TYPES = {"xlsx", "pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class EstimateFileResponse(BaseModel):
    id: str
    estimate_id: str
    file_name: str
    file_type: str
    file_size: int
    customer_name: Optional[str] = None
    total_price: Optional[float] = None
    created_at: Optional[str] = None


@router.post("", response_model=EstimateFileResponse, status_code=201, summary="견적 파일 업로드")
async def upload_estimate_file(
    file: UploadFile = File(..., description="Excel 또는 PDF 파일"),
    estimate_id: str = Form(..., description="견적 ID"),
    customer_name: Optional[str] = Form(None, description="고객명"),
    total_price: Optional[float] = Form(None, description="총액"),
    db: AsyncSession = Depends(get_db),
) -> EstimateFileResponse:
    """견적 파일(Excel/PDF)을 데이터베이스에 저장합니다."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"허용되지 않는 파일 형식입니다: {ext}")

    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 50MB를 초과합니다")

    service = EstimateFileService()
    try:
        await service.ensure_table(db)
    except Exception:
        logger.warning("Table ensure_table failed (may already exist)")

    result = await service.save_file(
        db, estimate_id, file.filename, ext, file_data, customer_name, total_price,
    )
    await db.commit()

    return EstimateFileResponse(
        id=result["id"],
        estimate_id=result["estimate_id"],
        file_name=result["file_name"],
        file_type=result["file_type"],
        file_size=result["file_size"],
        customer_name=result.get("customer_name"),
        total_price=float(result["total_price"]) if result.get("total_price") else None,
        created_at=str(result["created_at"]) if result.get("created_at") else None,
    )


@router.get("", response_model=List[EstimateFileResponse], summary="견적 파일 목록 조회")
async def list_estimate_files(
    search: Optional[str] = Query(None, description="견적ID/파일명/고객명 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[EstimateFileResponse]:
    """저장된 견적 파일 목록을 조회합니다."""
    service = EstimateFileService()
    try:
        await service.ensure_table(db)
    except Exception:
        pass

    results = await service.list_files(db, search, skip, limit)
    return [
        EstimateFileResponse(
            id=r["id"],
            estimate_id=r["estimate_id"],
            file_name=r["file_name"],
            file_type=r["file_type"],
            file_size=r["file_size"],
            customer_name=r.get("customer_name"),
            total_price=float(r["total_price"]) if r.get("total_price") else None,
            created_at=str(r["created_at"]) if r.get("created_at") else None,
        )
        for r in results
    ]


@router.get("/{file_id}/download", summary="견적 파일 다운로드")
async def download_estimate_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """견적 파일을 다운로드합니다."""
    service = EstimateFileService()
    result = await service.get_file_data(db, file_id)
    if not result:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    content_types = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
    }
    content_type = content_types.get(result["file_type"], "application/octet-stream")

    return Response(
        content=bytes(result["file_data"]),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result["file_name"]}"',
            "Content-Length": str(result["file_size"]),
        },
    )


@router.delete("/{file_id}", status_code=204, summary="견적 파일 삭제")
async def delete_estimate_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """견적 파일을 삭제합니다."""
    service = EstimateFileService()
    success = await service.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    await db.commit()
