# Regression Test Golden Set

**Purpose**: Ensure core functionality never breaks across code changes

**Verification Method**: Input → Output byte-level equality (hash verification)

## Golden Set Tests (Phase I)

### 1. Full Pipeline Test (20/20 Required)
**File**: `tests/integration/test_stage1_2_3_pipeline.py`
**Marker**: `@pytest.mark.regression`
**Coverage**:
- Stage 1: Enclosure calculation
- Stage 2: Breaker placement
- Stage 3: Excel generation
- Quality gates verification

### 2. Real E2E API Test
**File**: `tests/integration/test_real_e2e_full_verbs.py`
**Marker**: `@pytest.mark.regression`
**Coverage**:
- POST /v1/estimate (create)
- GET /v1/estimate/{id} (retrieve)
- Full request/response cycle
- Error handling

### 3. Evidence Pack Generation
**File**: `tests/e2e/test_pipeline_evidence_v2.py`
**Marker**: `@pytest.mark.regression`
**Coverage**:
- Evidence artifact generation
- PDF/XLSX/SVG/JSON output
- Metadata integrity

## Execution Requirements

### Command
```bash
pytest -m regression -v --tb=short
```

### Success Criteria
- **All tests PASS**: 20/20 (100%)
- **No regressions**: Output hash matches golden baseline
- **Performance**: Total time < 30s (목표: < 20s)

### Baseline Snapshot
- **Created**: Phase I (2025-10-14)
- **Location**: `tests/regression/baseline_snapshot.json`
- **Update Policy**: Only on intentional contract changes with approval

## Future Enhancement (Phase I+1)

### CEO Real Estimates (Recommended)
**Source**: 대표님 실전 견적 5건
**Purpose**: Real-world scenario validation
**Files**: `tests/regression/golden_*_ceo_*.py`

**Scenarios**:
1. `golden_001_ceo_industrial_complex.py` - 산업단지 대용량 (800AF 메인)
2. `golden_002_ceo_commercial_building.py` - 상업건물 중규모 (200AF 메인)
3. `golden_003_ceo_residential_complex.py` - 주거단지 소규모 (100AF 메인)
4. `golden_004_ceo_factory_magnet.py` - 공장 마그네트 다수 (부속자재 검증)
5. `golden_005_ceo_multi_panel.py` - 다중 분전반 (2개 이상)

### Verification Method
```python
# Input hash (frozen)
input_hash = sha256(json.dumps(request_data, sort_keys=True))

# Output hash (must match baseline)
output_hash = sha256(json.dumps(response_data, sort_keys=True))

assert output_hash == BASELINE_HASH, "Regression detected!"
```

## DoD (Definition of Done)

- [x] 회귀 테스트 3종 선정
- [x] @pytest.mark.regression 적용
- [ ] Baseline snapshot 생성 (baseline_snapshot.json)
- [ ] CI에서 regression 게이트 추가
- [ ] 대표님 실전 견적 5건 추가 (Phase I+1)

## Rollback Policy

If regression detected:
1. **Identify**: Which test failed?
2. **Analyze**: Intentional contract change or bug?
3. **Decide**:
   - Bug → Fix immediately
   - Contract change → Get approval, update baseline
4. **Verify**: Re-run regression suite

---

**Status**: DRAFT
**Owner**: Narberal Gamma
**Last Updated**: 2025-10-14 Phase I
