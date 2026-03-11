"""
RAG API Endpoints - FastAPI 라우터

/v1/rag/search - 지식 검색
/v1/rag/stats - 인덱스 통계
/v1/rag/learn - 지식 학습 (저장)
/v1/rag/learned - 학습된 지식 조회
"""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from kis_estimator_core.rag.config import RAGConfig
from kis_estimator_core.rag.learner import (
    LearningCategory,
    get_learner,
)
from kis_estimator_core.rag.retriever import HybridRetriever

router = APIRouter(prefix="/v1/rag", tags=["RAG"])


# Request/Response Models
class SearchRequest(BaseModel):
    """검색 요청"""

    query: str = Field(..., min_length=1, max_length=500, description="검색 쿼리")
    category: str | None = Field(
        None, description="카테고리 필터 (BREAKER, ENCLOSURE, ACCESSORY, FORMULA, STANDARD, PRICE, RULE)"
    )
    top_k: int = Field(5, ge=1, le=20, description="반환할 결과 수")
    search_type: Literal["semantic", "keyword", "hybrid"] = Field(
        "hybrid", description="검색 유형"
    )


class SearchResultItem(BaseModel):
    """검색 결과 항목"""

    id: str
    content: str
    score: float
    category: str
    source: str
    search_type: str


class SearchResponse(BaseModel):
    """검색 응답"""

    query: str
    total: int
    results: list[SearchResultItem]


class StatsResponse(BaseModel):
    """통계 응답"""

    total_chunks: int
    collection_name: str
    embedding_model: str
    categories: dict[str, int]


# Singleton retriever (lazy init)
_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    """Retriever 싱글톤 인스턴스"""
    global _retriever
    if _retriever is None:
        config = RAGConfig()
        _retriever = HybridRetriever(config)
    return _retriever


# Endpoints
@router.post("/search", response_model=SearchResponse)
async def search_knowledge(request: SearchRequest):
    """
    지식 베이스 검색

    하이브리드 검색 (Semantic + Keyword)을 통해 관련 지식을 검색합니다.
    """
    try:
        retriever = get_retriever()
        results = retriever.search(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            search_type=request.search_type,
        )

        return SearchResponse(
            query=request.query,
            total=len(results),
            results=[
                SearchResultItem(
                    id=r.id,
                    content=r.content,
                    score=r.score,
                    category=r.metadata.get("category", "UNKNOWN"),
                    source=r.metadata.get("source", ""),
                    search_type=r.source,
                )
                for r in results
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}") from e


@router.get("/search", response_model=SearchResponse)
async def search_knowledge_get(
    q: str = Query(..., min_length=1, max_length=500, description="검색 쿼리"),
    category: str | None = Query(None, description="카테고리 필터"),
    top_k: int = Query(5, ge=1, le=20, description="반환할 결과 수"),
):
    """
    지식 베이스 검색 (GET)

    간단한 검색을 위한 GET 엔드포인트
    """
    request = SearchRequest(query=q, category=category, top_k=top_k)
    return await search_knowledge(request)


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    인덱스 통계

    현재 인덱싱된 지식의 통계를 반환합니다.
    """
    try:
        from kis_estimator_core.rag.indexer import VectorIndexer

        config = RAGConfig()
        indexer = VectorIndexer(config)
        stats = indexer.get_stats()

        return StatsResponse(
            total_chunks=stats["total_chunks"],
            collection_name=stats["collection_name"],
            embedding_model=stats["embedding_model"],
            categories=stats.get("categories_sample", {}),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}") from e


@router.get("/categories")
async def get_categories():
    """
    사용 가능한 카테고리 목록
    """
    config = RAGConfig()
    return {"categories": config.categories}


@router.post("/breaker/search", response_model=SearchResponse)
async def search_breaker(
    q: str = Query(..., description="차단기 검색 쿼리"),
    top_k: int = Query(5, ge=1, le=20),
):
    """차단기 정보 검색"""
    request = SearchRequest(query=q, category="BREAKER", top_k=top_k)
    return await search_knowledge(request)


@router.post("/enclosure/search", response_model=SearchResponse)
async def search_enclosure(
    q: str = Query(..., description="외함 검색 쿼리"),
    top_k: int = Query(5, ge=1, le=20),
):
    """외함 정보 검색"""
    request = SearchRequest(query=q, category="ENCLOSURE", top_k=top_k)
    return await search_knowledge(request)


@router.post("/accessory/search", response_model=SearchResponse)
async def search_accessory(
    q: str = Query(..., description="부속자재 검색 쿼리"),
    top_k: int = Query(5, ge=1, le=20),
):
    """부속자재 정보 검색"""
    request = SearchRequest(query=q, category="ACCESSORY", top_k=top_k)
    return await search_knowledge(request)


@router.post("/formula/search", response_model=SearchResponse)
async def search_formula(
    q: str = Query(..., description="공식/규칙 검색 쿼리"),
    top_k: int = Query(5, ge=1, le=20),
):
    """공식/규칙 검색"""
    request = SearchRequest(query=q, category="FORMULA", top_k=top_k)
    return await search_knowledge(request)


# ========== 학습 (Learning) API ==========

# Learning Request/Response Models
class LearnKnowledgeRequest(BaseModel):
    """지식 학습 요청"""

    title: str = Field(..., min_length=1, max_length=200, description="제목")
    content: str = Field(..., min_length=1, max_length=5000, description="내용")
    category: Literal["KNOWLEDGE", "KNOWHOW", "PRICE", "RULE"] = Field(
        "KNOWLEDGE", description="카테고리"
    )
    tags: list[str] = Field(default_factory=list, description="태그 목록")
    source: str = Field("대화", description="학습 출처")


class LearnPriceRequest(BaseModel):
    """가격 학습 요청"""

    item_name: str = Field(..., min_length=1, max_length=200, description="품목명")
    new_price: int = Field(..., gt=0, description="새 가격")
    item_code: str = Field("", description="품목 코드")
    old_price: int | None = Field(None, description="이전 가격")
    reason: str = Field("", description="변경 사유")
    source: str = Field("대화", description="출처")


class LearnedItemResponse(BaseModel):
    """학습된 항목 응답"""

    id: str
    category: str
    title: str
    content: str
    source: str
    tags: list[str]
    created_at: str
    hash: str


class LearnedPriceResponse(BaseModel):
    """학습된 가격 응답"""

    id: str
    item_name: str
    item_code: str
    old_price: int | None
    new_price: int
    effective_date: str
    reason: str
    source: str
    created_at: str


class LearningStatsResponse(BaseModel):
    """학습 통계 응답"""

    total: int
    by_category: dict[str, int]
    last_updated: str | None


# Learning Endpoints
@router.post("/learn/knowledge", response_model=LearnedItemResponse)
async def learn_knowledge(request: LearnKnowledgeRequest):
    """
    지식 학습 (저장)

    대화 중 학습된 분전반/차단기/외함 관련 지식을 저장합니다.

    카테고리:
    - KNOWLEDGE: 기술 지식
    - KNOWHOW: 견적 노하우
    - RULE: 비즈니스 규칙
    """
    try:
        learner = get_learner()
        item = learner.save_knowledge(
            title=request.title,
            content=request.content,
            category=request.category,
            tags=request.tags,
            source=request.source,
        )

        return LearnedItemResponse(
            id=item.id,
            category=item.category,
            title=item.title,
            content=item.content,
            source=item.source,
            tags=item.tags,
            created_at=item.created_at,
            hash=item.hash,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"학습 저장 실패: {str(e)}") from e


@router.post("/learn/price", response_model=LearnedPriceResponse)
async def learn_price(request: LearnPriceRequest):
    """
    가격 학습 (저장)

    새로운 단가 정보를 저장합니다.
    """
    try:
        learner = get_learner()
        price_item = learner.save_price(
            item_name=request.item_name,
            new_price=request.new_price,
            item_code=request.item_code,
            old_price=request.old_price,
            reason=request.reason,
            source=request.source,
        )

        return LearnedPriceResponse(
            id=price_item.id,
            item_name=price_item.item_name,
            item_code=price_item.item_code,
            old_price=price_item.old_price,
            new_price=price_item.new_price,
            effective_date=price_item.effective_date,
            reason=price_item.reason,
            source=price_item.source,
            created_at=price_item.created_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가격 저장 실패: {str(e)}") from e


@router.post("/learn/knowhow", response_model=LearnedItemResponse)
async def learn_knowhow(
    title: str = Query(..., description="제목"),
    content: str = Query(..., description="내용"),
    tags: list[str] = Query(default=["견적", "노하우"], description="태그"),
):
    """
    노하우 학습 (간편 저장)

    예: "4P 50AF는 경제형이 없어서 표준형 사용해야 해"
    """
    request = LearnKnowledgeRequest(
        title=title,
        content=content,
        category="KNOWHOW",
        tags=tags,
        source="대화",
    )
    return await learn_knowledge(request)


@router.get("/learned", response_model=list[dict])
async def get_learned(
    category: Literal["KNOWLEDGE", "KNOWHOW", "PRICE", "RULE"] | None = Query(
        None, description="카테고리 필터"
    ),
    limit: int = Query(50, ge=1, le=200, description="최대 결과 수"),
):
    """
    학습된 지식 조회

    저장된 모든 학습 데이터를 조회합니다.
    """
    try:
        learner = get_learner()
        items = learner.get_all(category)
        return items[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}") from e


@router.get("/learned/search")
async def search_learned(
    q: str = Query(..., min_length=1, description="검색어"),
    category: Literal["KNOWLEDGE", "KNOWHOW", "PRICE", "RULE"] | None = Query(
        None, description="카테고리 필터"
    ),
    limit: int = Query(10, ge=1, le=50, description="최대 결과 수"),
):
    """
    학습된 지식 검색

    키워드로 학습된 데이터를 검색합니다.
    """
    try:
        learner = get_learner()
        results = learner.search(q, category, limit)
        return {"query": q, "total": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}") from e


@router.get("/learned/recent")
async def get_recent_learned(
    limit: int = Query(10, ge=1, le=50, description="최대 결과 수"),
):
    """
    최근 학습 데이터 조회
    """
    try:
        learner = get_learner()
        items = learner.get_recent(limit)
        return {"total": len(items), "items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}") from e


@router.get("/learned/stats", response_model=LearningStatsResponse)
async def get_learning_stats():
    """
    학습 데이터 통계
    """
    try:
        learner = get_learner()
        stats = learner.get_stats()
        return LearningStatsResponse(
            total=stats["total"],
            by_category=stats["by_category"],
            last_updated=stats.get("last_updated"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}") from e


@router.delete("/learned/{item_id}")
async def delete_learned(
    item_id: str,
    category: Literal["KNOWLEDGE", "KNOWHOW", "PRICE", "RULE"] = Query(
        ..., description="카테고리"
    ),
):
    """
    학습 데이터 삭제
    """
    try:
        learner = get_learner()
        success = learner.delete(item_id, category)

        if success:
            return {"status": "deleted", "id": item_id}
        else:
            raise HTTPException(status_code=404, detail=f"항목을 찾을 수 없음: {item_id}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}") from e
