# AI 매니저 시스템 개발계획서

**날짜**: 2025-12-07
**목표**: 자연어 쿼리로 데이터 분석, 그래프 생성, 보고서 작성이 가능한 AI 매니저 구축
**스킬**: writing-plans, systematic-debugging, test-driven-development
**원칙**: 목업금지, 빈파일금지, SSOT준수, 일관성있는코드작성

---

## 📋 Goal (목표)

**AI 매니저**가 ERP 시스템의 모든 데이터에 접근하여 자연어 명령으로 다음 작업을 수행:
1. 데이터 조회 ("한국산업에 7월에 판매한 금액 알려줘")
2. 데이터 분석 및 그래프 생성 ("1분기 2분기 매출 비교")
3. A4 2장 분량 보고서 자동 작성 (텍스트 + 그래프)
4. 모든 ERP 메뉴 접근/통제/수정 권한 (슈퍼 관리자)

---

## 🏗️ Architecture (아키텍처)

### 전체 시스템 구조
```
[Frontend: AI Manager Tab]
  ↓ User: "한국산업에 7월에 판매한 금액 알려줘"
[Backend: AI Manager Service]
  ↓ 1. 자연어 파싱 (LLM API)
  ↓ 2. Intent 분석 (Query/Analysis/Report)
  ↓ 3. SQL 생성 (Text-to-SQL)
  ↓ 4. PostgreSQL 쿼리 실행
  ↓ 5. 결과 분석 (Data Analysis)
  ↓ 6. 그래프 생성 (Chart.js, Recharts)
  ↓ 7. 보고서 작성 (PDF Generation)
[Frontend: Results Display]
  ↓ 텍스트 + 그래프 + 다운로드 링크
```

### 데이터 흐름
```
자연어 입력
  → LLM 파싱 (Claude/OpenAI)
  → Intent Classification
     ├─ "query" → SQL 생성 → 실행 → 결과 반환
     ├─ "analyze" → SQL + 분석 → 인사이트 생성
     └─ "report" → SQL + 분석 + 그래프 → PDF 생성
```

### 권한 시스템
```python
class AIManagerPermissions:
    """AI 매니저 슈퍼 권한"""
    CAN_READ_ALL = True  # 모든 데이터 조회
    CAN_WRITE_ALL = True  # 모든 데이터 수정
    CAN_DELETE_ALL = True  # 모든 데이터 삭제
    CAN_CONTROL_MENUS = True  # 메뉴 통제
    CAN_GENERATE_REPORTS = True  # 보고서 생성
    CAN_MODIFY_SETTINGS = True  # 시스템 설정 변경
```

---

## 🛠️ Tech Stack (기술 스택)

### Backend
- **LLM API**: Anthropic Claude 3.5 Sonnet (자연어 처리)
- **Text-to-SQL**: LLM + Few-shot Learning
- **데이터베이스**: PostgreSQL (Supabase)
- **데이터 분석**: Pandas, NumPy
- **그래프 생성**: Matplotlib, Plotly
- **PDF 생성**: ReportLab, WeasyPrint
- **API**: FastAPI

### Frontend
- **UI 프레임워크**: React + TypeScript
- **차트 라이브러리**: Recharts, Chart.js
- **자연어 입력창**: Textarea with streaming response
- **파일 다운로드**: FileSaver.js

### AI/ML
- **임베딩**: OpenAI text-embedding-ada-002
- **벡터 DB**: Pinecone (RAG용 스키마 저장)
- **프롬프트 템플릿**: Jinja2

---

## ✅ Tasks (작업 목록)

### Phase 1: 기반 인프라 구축 (8시간)

#### Task 1.1: SSOT 상수 정의 - AI 매니저 (2분)
**파일**: `src/kis_estimator_core/core/ssot/constants.py`

```python
# ============================================================
# AI 매니저 관련 상수 (AI Manager)
# ============================================================

# AI 매니저 Intent 타입
INTENT_QUERY = "query"  # 단순 데이터 조회
INTENT_ANALYZE = "analyze"  # 데이터 분석
INTENT_REPORT = "report"  # 보고서 생성
INTENT_CONTROL = "control"  # 시스템 통제

# LLM 모델
LLM_MODEL_CLAUDE = "claude-3-5-sonnet-20241022"
LLM_MODEL_GPT4 = "gpt-4-turbo-preview"

# 보고서 길이
REPORT_LENGTH_SHORT = "short"  # A4 1장
REPORT_LENGTH_MEDIUM = "medium"  # A4 2장
REPORT_LENGTH_LONG = "long"  # A4 3장 이상

# 오류 코드
ERROR_CODE_AI_PARSE_FAILED = "E_AI_001"  # 자연어 파싱 실패
ERROR_CODE_SQL_GENERATION_FAILED = "E_AI_002"  # SQL 생성 실패
ERROR_CODE_NO_DATA_FOUND = "E_AI_003"  # 데이터 없음
```

**Commit**:
```bash
git add src/kis_estimator_core/core/ssot/constants.py
git commit -m "feat: Add SSOT constants for AI Manager"
```

---

#### Task 1.2: PostgreSQL 스키마 설계 및 마이그레이션 (6시간)

**목표**: JSON 파일을 PostgreSQL로 이전

**마이그레이션 스크립트**: `scripts/migrate_json_to_postgres.py`

```python
"""
JSON 파일을 PostgreSQL로 마이그레이션

실행: python scripts/migrate_json_to_postgres.py
"""

import json
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime

# Supabase 연결 (환경변수에서 읽기)
DATABASE_URL = os.getenv("SUPABASE_DB_URL")
engine = create_engine(DATABASE_URL)

def migrate_customers():
    """거래처 데이터 마이그레이션"""
    customers_file = Path("data/erp/customers.json")

    with open(customers_file, "r", encoding="utf-8") as f:
        customers = json.load(f)

    with engine.connect() as conn:
        for customer in customers:
            conn.execute(text("""
                INSERT INTO erp.customers (
                    id, code, name, customer_type, grade,
                    business_number, ceo_name, contact_person,
                    phone, fax, email, address,
                    credit_limit, receivable, payable,
                    payment_terms, memo, is_active,
                    created_at, updated_at
                ) VALUES (
                    :id, :code, :name, :customer_type, :grade,
                    :business_number, :ceo_name, :contact_person,
                    :phone, :fax, :email, :address,
                    :credit_limit, :receivable, :payable,
                    :payment_terms, :memo, :is_active,
                    :created_at, :updated_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    receivable = EXCLUDED.receivable,
                    updated_at = EXCLUDED.updated_at
            """), customer)
        conn.commit()

    print(f"✅ {len(customers)}개 거래처 마이그레이션 완료")


def migrate_products():
    """상품 데이터 마이그레이션"""
    # 동일한 패턴으로 구현
    pass


def migrate_sales():
    """매출전표 데이터 마이그레이션"""
    # 동일한 패턴으로 구현
    pass


if __name__ == "__main__":
    migrate_customers()
    migrate_products()
    migrate_sales()
    print("🎉 전체 마이그레이션 완료")
```

**Alembic 마이그레이션**: `alembic/versions/001_create_erp_tables.py`

```python
"""
ERP 테이블 생성

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # erp 스키마 생성
    op.execute("CREATE SCHEMA IF NOT EXISTS erp")

    # customers 테이블
    op.create_table(
        'customers',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('customer_type', sa.String(20)),
        sa.Column('grade', sa.String(10)),
        sa.Column('business_number', sa.String(20)),
        sa.Column('ceo_name', sa.String(100)),
        sa.Column('contact_person', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('fax', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('address', sa.Text()),
        sa.Column('credit_limit', sa.Numeric(15, 2), default=0),
        sa.Column('receivable', sa.Numeric(15, 2), default=0),
        sa.Column('payable', sa.Numeric(15, 2), default=0),
        sa.Column('payment_terms', sa.String(100)),
        sa.Column('memo', sa.Text()),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), onupdate=sa.func.now()),
        schema='erp'
    )

    # products 테이블
    op.create_table(
        'products',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('spec', sa.String(200)),
        sa.Column('unit', sa.String(20)),
        sa.Column('category_id', sa.String(50)),
        sa.Column('purchase_price', sa.Numeric(15, 2), default=0),
        sa.Column('selling_price', sa.Numeric(15, 2), default=0),
        sa.Column('safety_stock', sa.Integer, default=0),
        sa.Column('current_stock', sa.Integer, default=0),
        sa.Column('memo', sa.Text()),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), onupdate=sa.func.now()),
        schema='erp'
    )

    # sales 테이블
    op.create_table(
        'sales',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('sale_number', sa.String(50), unique=True, nullable=False),
        sa.Column('sale_date', sa.Date, nullable=False),
        sa.Column('customer_id', sa.String(50), sa.ForeignKey('erp.customers.id')),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('supply_amount', sa.Numeric(15, 2), default=0),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0),
        sa.Column('total_amount', sa.Numeric(15, 2), default=0),
        sa.Column('cost_amount', sa.Numeric(15, 2), default=0),
        sa.Column('profit_amount', sa.Numeric(15, 2), default=0),
        sa.Column('memo', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), onupdate=sa.func.now()),
        schema='erp'
    )

    # sale_items 테이블
    op.create_table(
        'sale_items',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('sale_id', sa.String(50), sa.ForeignKey('erp.sales.id', ondelete='CASCADE')),
        sa.Column('product_id', sa.String(50), sa.ForeignKey('erp.products.id')),
        sa.Column('product_code', sa.String(20)),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('spec', sa.String(200)),
        sa.Column('unit', sa.String(20)),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('supply_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('cost_price', sa.Numeric(15, 2)),
        sa.Column('memo', sa.Text()),
        schema='erp'
    )

    # 인덱스 생성 (조회 성능 향상)
    op.create_index('idx_sales_date', 'sales', ['sale_date'], schema='erp')
    op.create_index('idx_sales_customer', 'sales', ['customer_id'], schema='erp')
    op.create_index('idx_customers_name', 'customers', ['name'], schema='erp')
    op.create_index('idx_products_name', 'products', ['name'], schema='erp')

def downgrade():
    op.drop_table('sale_items', schema='erp')
    op.drop_table('sales', schema='erp')
    op.drop_table('products', schema='erp')
    op.drop_table('customers', schema='erp')
    op.execute("DROP SCHEMA IF EXISTS erp CASCADE")
```

**실행**:
```bash
# 1. Alembic 마이그레이션
alembic upgrade head

# 2. 데이터 이전
python scripts/migrate_json_to_postgres.py
```

**Commit**:
```bash
git add alembic/versions/001_create_erp_tables.py scripts/migrate_json_to_postgres.py
git commit -m "feat: PostgreSQL schema and JSON migration"
```

---

### Phase 2: AI 매니저 백엔드 (12시간)

#### Task 2.1: LLM 서비스 구현 (3시간)

**파일**: `src/kis_estimator_core/services/llm_service.py`

```python
"""
LLM 서비스 (Claude API 통합)

기능:
1. 자연어 → Intent 분류
2. 자연어 → SQL 변환
3. 데이터 → 인사이트 생성
"""

import anthropic
from typing import Dict, Any, List
from src.kis_estimator_core.core.ssot.constants import (
    LLM_MODEL_CLAUDE,
    INTENT_QUERY,
    INTENT_ANALYZE,
    INTENT_REPORT,
)


class LLMService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = LLM_MODEL_CLAUDE

    def classify_intent(self, user_input: str) -> str:
        """자연어 입력을 Intent로 분류"""
        prompt = f"""
다음 사용자 입력을 분석하여 Intent를 분류하세요.

사용자 입력: "{user_input}"

Intent 종류:
- query: 단순 데이터 조회 (예: "한국산업에 7월에 판매한 금액 알려줘")
- analyze: 데이터 분석 (예: "1분기 2분기 매출 비교해줘")
- report: 보고서 생성 (예: "매출 보고서를 A4 2장으로 작성해줘")

응답 형식: {{"intent": "query|analyze|report"}}
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        import json
        result = json.loads(response_text)
        return result["intent"]

    def generate_sql(self, user_input: str, schema: Dict[str, Any]) -> str:
        """자연어 → SQL 변환 (Few-shot Learning)"""
        prompt = f"""
사용자 요청을 PostgreSQL 쿼리로 변환하세요.

데이터베이스 스키마:
{schema}

예시:
사용자: "한국산업에 7월에 판매한 금액 알려줘"
SQL: SELECT SUM(total_amount) FROM erp.sales WHERE customer_id IN (SELECT id FROM erp.customers WHERE name = '한국산업') AND EXTRACT(MONTH FROM sale_date) = 7

사용자: "1분기 2분기 매출 비교해줘"
SQL: SELECT EXTRACT(QUARTER FROM sale_date) AS quarter, SUM(total_amount) AS total FROM erp.sales WHERE EXTRACT(QUARTER FROM sale_date) IN (1, 2) GROUP BY quarter

사용자 요청: "{user_input}"
SQL:
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text.strip()

    def generate_insights(self, data: List[Dict], query: str) -> str:
        """데이터를 분석하여 인사이트 생성"""
        prompt = f"""
다음 데이터를 분석하여 주요 인사이트를 제공하세요.

사용자 질문: "{query}"

데이터:
{data}

다음 형식으로 응답:
1. 주요 발견사항 (3-5개)
2. 추세 분석
3. 권장사항
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text
```

**테스트**: `tests/unit/test_llm_service.py`

```python
import pytest
from src.kis_estimator_core.services.llm_service import LLMService

def test_classify_intent_query():
    """Intent 분류 테스트 - query"""
    llm = LLMService(api_key="test_key")
    intent = llm.classify_intent("한국산업에 7월에 판매한 금액 알려줘")
    assert intent == "query"

def test_classify_intent_analyze():
    """Intent 분류 테스트 - analyze"""
    llm = LLMService(api_key="test_key")
    intent = llm.classify_intent("1분기 2분기 매출 비교해줘")
    assert intent == "analyze"
```

**Commit**:
```bash
git add src/kis_estimator_core/services/llm_service.py tests/unit/test_llm_service.py
git commit -m "feat: Implement LLM service for AI Manager"
```

---

#### Task 2.2: AI 매니저 API 엔드포인트 (4시간)

**파일**: `src/kis_estimator_core/api/routes/ai_manager.py`

```python
"""
AI 매니저 API 라우터

엔드포인트:
- POST /ai-manager/query: 자연어 쿼리 처리
- POST /ai-manager/report: 보고서 생성
- GET /ai-manager/insights: 자동 인사이트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from src.kis_estimator_core.services.llm_service import LLMService
from src.kis_estimator_core.core.ssot.constants import (
    INTENT_QUERY,
    INTENT_ANALYZE,
    INTENT_REPORT,
    ERROR_CODE_AI_PARSE_FAILED,
    ERROR_CODE_SQL_GENERATION_FAILED,
)

router = APIRouter(prefix="/ai-manager", tags=["AI Manager"])

# LLM 서비스 초기화
llm_service = LLMService(api_key=os.getenv("ANTHROPIC_API_KEY"))

# PostgreSQL 연결
engine = create_engine(os.getenv("SUPABASE_DB_URL"))


class QueryRequest(BaseModel):
    query: str  # 자연어 쿼리


class QueryResponse(BaseModel):
    intent: str  # query|analyze|report
    sql: str  # 생성된 SQL
    data: List[Dict[str, Any]]  # 조회 결과
    insights: str | None  # 인사이트 (analyze/report일 때)


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    자연어 쿼리 처리

    예시:
    - "한국산업에 7월에 판매한 금액 알려줘"
    - "1분기 2분기 매출 비교해줘"
    """
    try:
        # 1. Intent 분류
        intent = llm_service.classify_intent(request.query)

        # 2. SQL 생성
        schema = get_database_schema()  # 스키마 정보 조회
        sql = llm_service.generate_sql(request.query, schema)

        # 3. SQL 실행
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            data = [dict(row) for row in result]

        # 4. 인사이트 생성 (analyze/report일 때)
        insights = None
        if intent in [INTENT_ANALYZE, INTENT_REPORT]:
            insights = llm_service.generate_insights(data, request.query)

        return QueryResponse(
            intent=intent,
            sql=sql,
            data=data,
            insights=insights
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"쿼리 처리 실패: {str(e)}"
        )


def get_database_schema() -> Dict[str, Any]:
    """데이터베이스 스키마 정보 조회"""
    return {
        "customers": {
            "columns": ["id", "code", "name", "customer_type", "credit_limit", "receivable"],
            "description": "거래처 정보"
        },
        "products": {
            "columns": ["id", "code", "name", "spec", "unit", "selling_price", "current_stock"],
            "description": "상품 정보"
        },
        "sales": {
            "columns": ["id", "sale_number", "sale_date", "customer_id", "total_amount"],
            "description": "매출전표 정보"
        },
    }
```

**통합 테스트**: `tests/integration/test_ai_manager_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.kis_estimator_core.api.main import app

client = TestClient(app)

def test_ai_manager_query():
    """AI 매니저 쿼리 테스트"""
    response = client.post("/ai-manager/query", json={
        "query": "한국산업에 7월에 판매한 금액 알려줘"
    })

    assert response.status_code == 200
    result = response.json()
    assert result["intent"] == "query"
    assert "sql" in result
    assert "data" in result
```

**Commit**:
```bash
git add src/kis_estimator_core/api/routes/ai_manager.py tests/integration/test_ai_manager_api.py
git commit -m "feat: Implement AI Manager API endpoints"
```

---

#### Task 2.3: 그래프 생성 서비스 (3시간)

**파일**: `src/kis_estimator_core/services/chart_generator.py`

```python
"""
그래프 생성 서비스

기능:
1. 데이터 → 차트 타입 자동 선택
2. Matplotlib/Plotly로 그래프 생성
3. PNG/SVG 파일 저장
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 백엔드에서 GUI 없이 사용
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any


class ChartGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_chart(
        self,
        data: List[Dict[str, Any]],
        chart_type: str = "auto",
        title: str = "Chart"
    ) -> str:
        """
        데이터를 받아 그래프 생성

        Args:
            data: 데이터 리스트
            chart_type: bar/line/pie/auto
            title: 그래프 제목

        Returns:
            생성된 파일 경로
        """
        df = pd.DataFrame(data)

        # 자동 차트 타입 선택
        if chart_type == "auto":
            chart_type = self._detect_chart_type(df)

        # 그래프 생성
        plt.figure(figsize=(10, 6))

        if chart_type == "bar":
            self._create_bar_chart(df, title)
        elif chart_type == "line":
            self._create_line_chart(df, title)
        elif chart_type == "pie":
            self._create_pie_chart(df, title)

        # 파일 저장
        filename = f"chart_{title.replace(' ', '_')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return str(filepath)

    def _detect_chart_type(self, df: pd.DataFrame) -> str:
        """데이터 특성에 따라 적절한 차트 타입 선택"""
        if len(df.columns) == 2:
            # 2개 컬럼: bar chart
            return "bar"
        elif "date" in df.columns or "month" in df.columns:
            # 시계열 데이터: line chart
            return "line"
        else:
            return "bar"

    def _create_bar_chart(self, df: pd.DataFrame, title: str):
        """막대 그래프 생성"""
        x_col = df.columns[0]
        y_col = df.columns[1]

        plt.bar(df[x_col], df[y_col], color='#4A90E2')
        plt.title(title, fontsize=16, weight='bold')
        plt.xlabel(x_col, fontsize=12)
        plt.ylabel(y_col, fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)

    def _create_line_chart(self, df: pd.DataFrame, title: str):
        """선 그래프 생성"""
        x_col = df.columns[0]
        y_col = df.columns[1]

        plt.plot(df[x_col], df[y_col], marker='o', linewidth=2, color='#4A90E2')
        plt.title(title, fontsize=16, weight='bold')
        plt.xlabel(x_col, fontsize=12)
        plt.ylabel(y_col, fontsize=12)
        plt.grid(alpha=0.3)

    def _create_pie_chart(self, df: pd.DataFrame, title: str):
        """원 그래프 생성"""
        label_col = df.columns[0]
        value_col = df.columns[1]

        plt.pie(df[value_col], labels=df[label_col], autopct='%1.1f%%', startangle=90)
        plt.title(title, fontsize=16, weight='bold')
```

**Commit**:
```bash
git add src/kis_estimator_core/services/chart_generator.py
git commit -m "feat: Implement chart generation service"
```

---

#### Task 2.4: PDF 보고서 생성 서비스 (2시간)

**파일**: `src/kis_estimator_core/services/report_generator.py`

```python
"""
PDF 보고서 생성 서비스

기능:
1. 텍스트 + 그래프 + 표를 포함한 A4 PDF 생성
2. 템플릿 기반 레이아웃
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class ReportGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        title: str,
        insights: str,
        data: List[Dict[str, Any]],
        chart_paths: List[str]
    ) -> str:
        """
        A4 2장 분량 PDF 보고서 생성

        Args:
            title: 보고서 제목
            insights: AI가 생성한 인사이트 텍스트
            data: 표 데이터
            chart_paths: 그래프 이미지 경로 리스트

        Returns:
            생성된 PDF 파일 경로
        """
        filename = f"report_{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename

        # PDF 문서 생성
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []

        # 스타일
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        heading_style = styles['Heading2']
        body_style = styles['BodyText']

        # 1. 제목
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.5*cm))

        # 2. 작성일
        story.append(Paragraph(f"작성일: {datetime.now().strftime('%Y년 %m월 %d일')}", body_style))
        story.append(Spacer(1, 1*cm))

        # 3. 인사이트 텍스트
        story.append(Paragraph("📊 주요 발견사항", heading_style))
        story.append(Spacer(1, 0.3*cm))
        for line in insights.split('\n'):
            if line.strip():
                story.append(Paragraph(line, body_style))
                story.append(Spacer(1, 0.2*cm))

        story.append(Spacer(1, 1*cm))

        # 4. 그래프 삽입
        for chart_path in chart_paths:
            story.append(Paragraph("📈 분석 그래프", heading_style))
            story.append(Spacer(1, 0.3*cm))
            img = Image(chart_path, width=15*cm, height=10*cm)
            story.append(img)
            story.append(Spacer(1, 1*cm))

        # 5. 데이터 표
        if data:
            story.append(Paragraph("📋 상세 데이터", heading_style))
            story.append(Spacer(1, 0.3*cm))

            # 테이블 생성
            table_data = [list(data[0].keys())]  # 헤더
            for row in data[:10]:  # 최대 10개 행만 표시
                table_data.append(list(row.values()))

            table = Table(table_data)
            table.setStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#4A90E2'),
                ('TEXTCOLOR', (0, 0), (-1, 0), '#FFFFFF'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, '#CCCCCC')
            ])
            story.append(table)

        # PDF 빌드
        doc.build(story)

        return str(filepath)
```

**Commit**:
```bash
git add src/kis_estimator_core/services/report_generator.py
git commit -m "feat: Implement PDF report generation service"
```

---

### Phase 3: AI 매니저 프론트엔드 (8시간)

#### Task 3.1: AI 매니저 윈도우 UI (4시간)

**파일**: `frontend/src/components/erp/windows/AIManagerWindow.tsx`

```typescript
"use client";

import { useState } from "react";
import DraggableModal from "../common/DraggableModal";
import { api } from "@/lib/api";

interface AIManagerWindowProps {
  isOpen: boolean;
  onClose: () => void;
}

interface QueryResult {
  intent: string;
  sql: string;
  data: any[];
  insights: string | null;
}

export default function AIManagerWindow({ isOpen, onClose }: AIManagerWindowProps) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!query.trim()) {
      alert("질문을 입력하세요.");
      return;
    }

    setLoading(true);
    try {
      const response = await api.aiManager.query({ query });
      setResult(response);
    } catch (error) {
      alert(`오류: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DraggableModal isOpen={isOpen} onClose={onClose} title="AI 매니저" width="900px">
      <div className="p-6">
        {/* 자연어 입력창 */}
        <div className="mb-6">
          <label className="block mb-2 font-medium text-gray-700">
            AI에게 질문하세요
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 한국산업에 7월에 판매한 금액 알려줘"
            className="w-full h-24 rounded-md border px-4 py-3 text-sm focus:border-blue-500 focus:outline-none"
          />
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="mt-3 rounded-md bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? "처리 중..." : "실행"}
          </button>
        </div>

        {/* 결과 표시 */}
        {result && (
          <div className="space-y-4">
            {/* Intent */}
            <div className="rounded-md bg-gray-50 p-4">
              <h3 className="mb-2 font-semibold">분석 유형</h3>
              <span className="rounded bg-blue-100 px-3 py-1 text-sm text-blue-800">
                {result.intent}
              </span>
            </div>

            {/* SQL */}
            <div className="rounded-md bg-gray-50 p-4">
              <h3 className="mb-2 font-semibold">실행된 쿼리</h3>
              <pre className="overflow-x-auto rounded bg-gray-900 p-3 text-sm text-green-400">
                {result.sql}
              </pre>
            </div>

            {/* 데이터 */}
            <div className="rounded-md bg-gray-50 p-4">
              <h3 className="mb-2 font-semibold">조회 결과</h3>
              <div className="max-h-60 overflow-auto rounded border">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-100">
                    <tr>
                      {result.data.length > 0 &&
                        Object.keys(result.data[0]).map((key) => (
                          <th key={key} className="px-3 py-2 text-left font-medium">
                            {key}
                          </th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.data.map((row, idx) => (
                      <tr key={idx} className="border-b">
                        {Object.values(row).map((value: any, vidx) => (
                          <td key={vidx} className="px-3 py-2">
                            {typeof value === "number"
                              ? value.toLocaleString()
                              : String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 인사이트 */}
            {result.insights && (
              <div className="rounded-md bg-blue-50 p-4">
                <h3 className="mb-2 font-semibold text-blue-900">AI 분석 결과</h3>
                <div className="whitespace-pre-wrap text-sm text-gray-700">
                  {result.insights}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </DraggableModal>
  );
}
```

**Commit**:
```bash
git add frontend/src/components/erp/windows/AIManagerWindow.tsx
git commit -m "feat: Implement AI Manager window UI"
```

---

#### Task 3.2: API 클라이언트 업데이트 (1시간)

**파일**: `frontend/src/lib/api.ts`

**추가 내용** (파일 하단에 추가):

```typescript
// AI Manager API
export interface AIManagerQueryRequest {
  query: string;
}

export interface AIManagerQueryResponse {
  intent: string;
  sql: string;
  data: any[];
  insights: string | null;
}

export const api = {
  // ... (기존 코드)

  aiManager: {
    query: (data: AIManagerQueryRequest) => {
      return fetchAPI<AIManagerQueryResponse>("/ai-manager/query", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
  },
};
```

**Commit**:
```bash
git add frontend/src/lib/api.ts
git commit -m "feat: Add AI Manager API client"
```

---

#### Task 3.3: ERP 메인 윈도우에 AI 매니저 버튼 추가 (1시간)

**파일**: `frontend/src/components/erp/ERPWindowManager.tsx`

**수정**: AI 매니저 윈도우 import 및 상태 추가

```typescript
// ... (기존 import)
import AIManagerWindow from "./windows/AIManagerWindow";

// ... (기존 코드)

const [showAIManager, setShowAIManager] = useState(false);

// ... (기존 윈도우들)

{/* AI 매니저 윈도우 */}
<AIManagerWindow
  isOpen={showAIManager}
  onClose={() => setShowAIManager(false)}
/>
```

**파일**: `frontend/src/components/erp/ERPSidebar.tsx`

**수정**: AI 매니저 메뉴 버튼 추가

```typescript
<button
  onClick={() => onMenuClick("ai-manager")}
  className="flex items-center gap-2 rounded-md px-4 py-2 text-sm hover:bg-gray-100"
>
  🤖 AI 매니저
</button>
```

**Commit**:
```bash
git add frontend/src/components/erp/ERPWindowManager.tsx frontend/src/components/erp/ERPSidebar.tsx
git commit -m "feat: Add AI Manager button to ERP sidebar"
```

---

### Phase 4: 통합 테스트 및 최적화 (4시간)

#### Task 4.1: E2E 테스트 작성 (2시간)

**파일**: `tests/e2e/test_ai_manager.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('AI 매니저', () => {
  test('자연어 쿼리 실행', async ({ page }) => {
    // ERP 접속
    await page.goto('http://localhost:3000/erp');

    // AI 매니저 클릭
    await page.click('text=🤖 AI 매니저');

    // 자연어 입력
    await page.fill('textarea', '한국산업에 7월에 판매한 금액 알려줘');

    // 실행 버튼 클릭
    await page.click('button:has-text("실행")');

    // 결과 대기
    await expect(page.locator('text=분석 유형')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=실행된 쿼리')).toBeVisible();
    await expect(page.locator('text=조회 결과')).toBeVisible();
  });
});
```

**실행**:
```bash
npx playwright test tests/e2e/test_ai_manager.spec.ts
```

**Commit**:
```bash
git add tests/e2e/test_ai_manager.spec.ts
git commit -m "test: Add E2E tests for AI Manager"
```

---

#### Task 4.2: 성능 최적화 (2시간)

**최적화 항목**:
1. SQL 쿼리 인덱스 최적화
2. LLM API 응답 캐싱 (Redis)
3. 그래프 생성 비동기 처리 (Celery)

**파일**: `src/kis_estimator_core/services/cache_service.py`

```python
"""
캐시 서비스 (Redis)

기능:
- LLM 응답 캐싱 (동일 질문 반복 시 즉시 응답)
- TTL: 1시간
"""

import redis
import json
from typing import Optional

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    def get_cached_query(self, query: str) -> Optional[dict]:
        """캐시된 쿼리 결과 조회"""
        key = f"ai_query:{query}"
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    def cache_query(self, query: str, result: dict):
        """쿼리 결과 캐싱 (TTL 1시간)"""
        key = f"ai_query:{query}"
        self.redis.setex(key, 3600, json.dumps(result))
```

**Commit**:
```bash
git add src/kis_estimator_core/services/cache_service.py
git commit -m "feat: Add cache service for AI query optimization"
```

---

## 📊 예상 공수 및 일정

| Phase | 작업 | 예상 시간 | 우선순위 |
|-------|------|-----------|---------|
| Phase 1 | PostgreSQL 마이그레이션 | 8시간 | P1 (최우선) |
| Phase 2 | AI 매니저 백엔드 | 12시간 | P1 |
| Phase 3 | AI 매니저 프론트엔드 | 8시간 | P2 |
| Phase 4 | 통합 테스트 및 최적화 | 4시간 | P2 |
| **총계** | | **32시간** | |

**예상 완료일**: 약 4일 (1일 8시간 작업 기준)

---

## 🎯 다음 단계

### 즉시 시작 (오늘)
1. PostgreSQL 스키마 설계 및 Alembic 마이그레이션
2. JSON → PostgreSQL 데이터 이전

### 내일
1. LLM 서비스 구현 (Claude API 통합)
2. AI 매니저 API 엔드포인트

### 모레
1. 그래프 생성 서비스
2. PDF 보고서 생성 서비스
3. 프론트엔드 UI

### 4일차
1. 통합 테스트
2. 성능 최적화
3. 배포

---

## 🚨 주의사항

### 보안
- **API 키 보안**: ANTHROPIC_API_KEY는 환경변수에서만 읽기
- **SQL Injection 방지**: LLM이 생성한 SQL은 반드시 파라미터화
- **권한 검증**: AI 매니저는 관리자 권한 필수

### 데이터 정합성
- **트랜잭션 보장**: PostgreSQL ACID 준수
- **백업 자동화**: 일일 백업 스크립트

### 비용 관리
- **LLM API 호출 제한**: 분당 10회로 제한
- **캐싱 활용**: 동일 질문 반복 시 캐시 응답

---

*작성: 나베랄 감마*
*작성일: 2025-12-07*
*상태: 계획 완료, 실행 대기*
