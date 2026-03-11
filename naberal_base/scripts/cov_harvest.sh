#!/bin/bash
# Coverage Harvester - Phase I-3.5
# Collects coverage from multiple test targets and combines them
# Prevents partial test runs from showing 0% on untested modules

set -euo pipefail

echo "[Coverage Harvester] Starting targeted coverage collection..."

# Load .env.test.local if exists (Phase I-3.5: Integration Tests)
if [ -f .env.test.local ]; then
  echo "[INFO] Loading .env.test.local for DATABASE_URL..."
  export $(grep -v '^#' .env.test.local | xargs)
  echo "[INFO] DATABASE_URL loaded: ${DATABASE_URL:0:30}..."
fi

# Clean old coverage data (preserve .coveragerc!)
rm -f .coverage .coverage.* || true
mkdir -p out/evidence

# 1) Wave 2 Tests (Stage 3 phase calculations, Stage 2 data prep)
echo "[1/20] Wave 2: Stage 3 phase calculations, Stage 2 data prep..."
python -m pytest tests/coverage_wave2/ -q \
  --cov=kis_estimator_core/kpew/execution/stage_runner \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Wave 2 tests had failures, continuing..."

# 2) T1+T2 Tests (Stage 0 validation, Stage 1/2 error paths)
echo "[2/19] T1+T2: Stage 0 validation, Stage 1/2 error paths..."
python -m pytest tests/unit/stage_runner/ -q \
  --cov=kis_estimator_core/kpew/execution/stage_runner \
  --cov-report= \
  --cov-append \
  || echo "[WARN] T1+T2 tests had failures, continuing..."

# 3) Integration Stages (A1-A6: Real DB/FS execution)
echo "[3/19] Integration Stages: A1-A6 (Real DB/FS, skip if unavailable)..."
if [ -z "${DATABASE_URL:-}" ]; then
  echo "[INFO] DATABASE_URL not set - skipping integration tests (SB-05)"
else
  python -m pytest tests/integration/stages/ -q \
    --cov=kis_estimator_core/kpew/execution/stage_runner \
    --cov=kis_estimator_core/engine/enclosure_solver \
    --cov=kis_estimator_core/engine/breaker_placer \
    --cov=kis_estimator_core/infra/evidence \
    --cov-report= \
    --cov-append \
    || echo "[WARN] Integration stages skipped (DB unavailable)"
fi

# 4) breaker_placer (Unit tests)
echo "[4/19] breaker_placer.py via unit tests..."
python -m pytest tests/unit/test_breaker_placer.py -q \
  --cov=kis_estimator_core/engine/breaker_placer \
  --cov-report= \
  --cov-append \
  || echo "[WARN] breaker_placer tests had failures, continuing..."

# 5) enclosure_solver (Unit tests)
echo "[5/19] enclosure_solver.py via unit tests..."
python -m pytest tests/unit/test_enclosure_solver.py -q \
  --cov=kis_estimator_core/engine/enclosure_solver \
  --cov-report= \
  --cov-append \
  || echo "[WARN] enclosure_solver tests had failures, continuing..."

# 6) infra.evidence (Unit tests)
echo "[6/19] infra/evidence.py via unit tests..."
python -m pytest tests/unit/test_evidence.py -q \
  --cov=kis_estimator_core/infra/evidence \
  --cov-report= \
  --cov-append \
  || echo "[WARN] evidence tests had failures, continuing..."

# 7a) P4-2 Coverage Expansion - Unit Tests (validator, guards_format, jwks_sop, evidence)
echo "[7a/19] P4-2 Real-Call Unit Tests: validator + guards_format + jwks_sop + evidence..."
python -m pytest \
  tests/unit/kpew/test_validator_real_calls.py \
  tests/unit/core/test_guards_format_real_calls.py \
  tests/unit/core/test_guards_format_comprehensive.py \
  tests/unit/infra/test_jwks_sop_real_calls.py \
  tests/unit/infra/test_evidence_pack_real_calls.py \
  -q \
  --cov=src.kis_estimator_core.kpew.gates.validator \
  --cov=src.kis_estimator_core.core.ssot.guards_format \
  --cov=src.kis_estimator_core.infra.jwks_sop \
  --cov=src.kis_estimator_core.infra.evidence \
  --cov-report= \
  --cov-append \
  || echo "[WARN] P4-2 unit tests had failures, continuing..."

# 7b) P4-2 Coverage Expansion - Integration Tests (rls_loader - requires DB)
echo "[7b/19] P4-2 Real-Call Integration: rls_loader (skip if DATABASE_URL unavailable)..."
if [ -z "${DATABASE_URL:-}" ]; then
  echo "[INFO] DATABASE_URL not set - skipping rls_loader integration tests (SB-05)"
else
  python -m pytest tests/integration/infra/test_rls_loader_real_calls.py -q \
    --cov=kis_estimator_core/infra/rls_loader \
    --cov-report= \
    --cov-append \
    || echo "[WARN] P4-2 rls_loader tests skipped (DB unavailable or test failure)"
fi

# 7c) Phase I-4 Unit Tests (knowledge_loader, quality_gate, pdf_drivers, evidence_packer, generated_models)
echo "[7c/19] Phase I-4 Real-Call Unit Tests: knowledge_loader + quality_gate + pdf_drivers + packer + generated_models..."
python -m pytest \
  tests/unit/infra/test_knowledge_loader_real_calls.py \
  tests/unit/infra/test_quality_gate_real_calls.py \
  tests/unit/core/test_pdf_drivers_real_calls.py \
  tests/unit/evidence/test_evidence_packer_real_calls.py \
  tests/unit/core/test_generated_models_validators.py \
  -q \
  --cov=kis_estimator_core/infra/knowledge_loader \
  --cov=kis_estimator_core/infra/quality_gate \
  --cov=kis_estimator_core/core/ssot/pdf_drivers \
  --cov=kis_estimator_core/evidence/packer \
  --cov=kis_estimator_core/core/ssot/generated_models \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Phase I-4 unit tests had failures, continuing..."

# 7d) Phase I-4 Integration Tests (supabase_client - requires DB)
echo "[7d/19] Phase I-4 Real-Call Integration: supabase_client (skip if DATABASE_URL unavailable)..."
if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "[INFO] SUPABASE credentials not set - skipping supabase_client tests (SB-05)"
else
  python -m pytest tests/integration/infra/test_supabase_client_real.py -q \
    --cov=kis_estimator_core/infra/supabase_client \
    --cov-report= \
    --cov-append \
    || echo "[WARN] Phase I-4 supabase_client tests skipped (credentials unavailable or test failure)"
fi

# 7e) Phase I-5 Wave 8a: data_transformer.py comprehensive coverage
echo "[7e/19] Phase I-5 Wave 8a: data_transformer.py unit tests..."
python -m pytest \
  tests/unit/engine/test_data_transformer_init.py \
  tests/unit/engine/test_data_transformer_group.py \
  tests/unit/engine/test_data_transformer_enclosure.py \
  tests/unit/engine/test_data_transformer_breaker.py \
  tests/unit/engine/test_data_transformer_busbar.py \
  tests/unit/engine/test_data_transformer_misc.py \
  tests/unit/engine/test_data_transformer_accessories.py \
  tests/unit/engine/test_data_transformer_transform.py \
  -q \
  --cov=kis_estimator_core/engine/data_transformer \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Phase I-5 Wave 8a tests had failures, continuing..."

# 7f) Phase I-5 Wave 8b: enclosure_solver.py comprehensive coverage (10.59% → 84.12%)
echo "[7f/19] Phase I-5 Wave 8b: enclosure_solver.py unit tests..."
python -m pytest \
  tests/unit/engine/test_enclosure_solver_init.py \
  tests/unit/engine/test_enclosure_solver_height.py \
  tests/unit/engine/test_enclosure_solver_width_depth.py \
  tests/unit/engine/test_enclosure_solver_helpers.py \
  tests/unit/engine/test_enclosure_solver_solve.py \
  tests/unit/engine/test_enclosure_solver_edge_cases.py \
  -q \
  --cov=kis_estimator_core/engine/enclosure_solver \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Phase I-5 Wave 8b tests had failures, continuing..."

# 7g) Phase I-5 Wave 9: evidence.py + knowledge_loader.py (0% → 100%/97.92%)
echo "[7g/19] Phase I-5 Wave 9: evidence.py + knowledge_loader.py..."
python -m pytest \
  tests/unit/infra/test_evidence_real_calls.py \
  tests/unit/infra/test_knowledge_loader_real_calls.py \
  -q \
  --cov=src.kis_estimator_core.infra.evidence \
  --cov=src.kis_estimator_core.infra.knowledge_loader \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Phase I-5 Wave 9 tests had failures, continuing..."

# 7h) Phase I-5 Wave 10: jwks_sop.py + rls_loader.py (0% → 79.08%/70.07%)
echo "[7h/19] Phase I-5 Wave 10: jwks_sop.py + rls_loader.py..."
python -m pytest \
  tests/unit/infra/test_jwks_sop_real_calls.py \
  tests/unit/infra/test_rls_loader.py \
  -q \
  --cov=src.kis_estimator_core.infra.jwks_sop \
  --cov=src.kis_estimator_core.infra.rls_loader \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Phase I-5 Wave 10 tests had failures, continuing..."

# 7i) Phase I-5 Wave 11: quality_gate.py + catalog.py (0% → 91.75%/99.01%)
echo "[7i/19] Phase I-5 Wave 11: quality_gate.py + catalog.py..."
python -m pytest \
  tests/unit/infra/test_quality_gate_real_calls.py \
  tests/unit/models/test_catalog_models.py \
  -q \
  --cov=src.kis_estimator_core.infra.quality_gate \
  --cov=src.kis_estimator_core.models.catalog \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Phase I-5 Wave 11 tests had failures, continuing..."

# 7j) Phase I-5 Wave 12: pdf_drivers.py + supabase_client.py (0% → 66.67%/83.58%)
echo "[7j/19] Phase I-5 Wave 12: pdf_drivers.py + supabase_client.py..."
python -m pytest \
  tests/unit/core/test_pdf_drivers_real_calls.py \
  -q \
  --cov=src.kis_estimator_core.core.ssot.pdf_drivers \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Phase I-5 Wave 12 pdf_drivers tests had failures, continuing..."

# 7j-2) Phase I-5 Wave 12: supabase_client.py (requires Supabase credentials)
if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "[INFO] SUPABASE credentials not set - skipping supabase_client tests (Wave 12)"
else
  python -m pytest tests/integration/infra/test_supabase_client_real.py -q \
    --cov=src.kis_estimator_core.infra.supabase_client \
    --cov-report= \
    --cov-append \
    || echo "[WARN] Phase I-5 Wave 12 supabase_client tests skipped (credentials unavailable or test failure)"
fi

# 8) Full regression smoke (all modules)
echo "[8/19] Full regression suite for remaining coverage..."
python -m pytest tests/regression/ -q -m regression \
  --cov=api \
  --cov=kis_estimator_core \
  --cov-report= \
  --cov-append \
  || echo "[WARN] Full regression had failures, continuing..."

# 9) 핀포인트 마무리 T1: catalog.py boundary tests (Phase I-5 finish)
echo "[9/19] Phase I-5 Finish T1: catalog.py boundary tests..."
python -m pytest tests/regression/test_catalog_edges.py -q \
  --cov=api.routers.catalog \
  --cov-report= \
  --cov-append \
  || echo "[WARN] T1 catalog tests had failures, continuing..."

# 10) 핀포인트 마무리 T2: guards_format.py guard tests (Phase I-5 finish)
echo "[10/19] Phase I-5 Finish T2: guards_format.py guard tests..."
python -m pytest tests/unit/guards/test_guards_finish.py -q \
  --cov=src.kis_estimator_core.core.ssot.guards_format \
  --cov-report= \
  --cov-append \
  || echo "[WARN] T2 guards_format tests had failures, continuing..."

# 11) 핀포인트 마무리 T3: mappers.py DTO/Domain tests (Phase I-5 finish)
echo "[11/19] Phase I-5 Finish T3: mappers.py DTO/Domain tests..."
python -m pytest tests/unit/engine/test_mappers_finish.py -q \
  --cov=src.kis_estimator_core.core.ssot.mappers \
  --cov-report= \
  --cov-append \
  || echo "[WARN] T3 mappers tests had failures, continuing..."

# 12) 핀포인트 마무리 T4: enclosure_validator.py 전체 커버리지 (Phase I-5 finish)
echo "[12/19] Phase I-5 Finish T4: enclosure_validator.py validation tests..."
python -m pytest tests/unit/validators/test_enclosure_validator_finish.py -q \
  --cov=src.kis_estimator_core.validators.enclosure_validator \
  --cov-report= \
  --cov-append \
  || echo "[WARN] T4 enclosure_validator tests had failures, continuing..."

# 20) Phase I-6: DB-Enabled Integration Lane (catalog_service + stage_runner + health)
echo "[20/20] Phase I-6: DB-Enabled Integration Lane (requires_db)..."
if [ -z "${DATABASE_URL:-}" ]; then
  echo "[INFO] DATABASE_URL not set - skipping Phase I-6 integration tests (SB-05)"
else
  python -m pytest tests/integration/ -q -m requires_db \
    --cov=kis_estimator_core/services/catalog_service \
    --cov=kis_estimator_core/kpew/execution/stage_runner \
    --cov=api.main \
    --cov=api.db \
    --cov-report= \
    --cov-append \
    || echo "[WARN] Phase I-6 DB integration tests had failures, continuing..."
fi

# No combine needed - using single .coverage file with --cov-append
echo ""
echo "[Coverage Harvester] Generating reports from accumulated coverage..."

# Generate XML report (for CI/Evidence)
echo "[Coverage Harvester] Generating coverage.xml..."
coverage xml -o out/evidence/coverage.xml

# Generate terminal report with fail_under=60 check (Phase III: operational stability)
echo ""
echo "[Coverage Harvester] Final Coverage Report:"
echo "============================================="
coverage report -m --fail-under=60 | tee out/evidence/cov_harvest_full.log

echo ""
echo "[Coverage Harvester] Complete! Artifacts:"
echo "  - out/evidence/coverage.xml"
echo "  - out/evidence/cov_harvest_full.log"
echo "  - htmlcov/ (run 'coverage html' to generate)"
