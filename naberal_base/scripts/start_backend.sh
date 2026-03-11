#!/bin/bash
cd "$(dirname "$0")/.."
export PYTHONPATH=".:src:${PYTHONPATH}"
exec python -m uvicorn src.kis_estimator_core.api.main:app --host 0.0.0.0 --port 8000
