#!/usr/bin/env bash
# 라쳇 메커니즘: 3회 연속 달성 시 다음 게이트 제안 (Phase VIII)
# Ladder: 60 (운영) → 62 → 65 → 70 (자동 상향)
# Usage: ./scripts/check_ratchet.sh [coverage_xml_path]

set -euo pipefail

COVERAGE_XML="${1:-coverage.xml}"
HISTORY_FILE=".coverage_history.txt"
RATCHET_THRESHOLD=68.0  # Phase VIII: 68% 3회 연속 → 70% 제안
CURRENT_GATE=66.0        # 현재 운영 게이트 (2025-11-28 상향)
TARGET_GATE=70.0         # 다음 목표 게이트
CONSECUTIVE_REQUIRED=3

# Coverage XML에서 line-rate 추출 (Python fallback for Windows)
get_coverage() {
    local coverage_xml="$1"
    if [[ ! -f "$coverage_xml" ]]; then
        echo "ERROR: Coverage file not found: $coverage_xml" >&2
        return 1
    fi

    # Python으로 백분율 변환 (bc 의존성 제거)
    python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$coverage_xml')
root = tree.getroot()
line_rate = float(root.attrib.get('line-rate', 0))
print(f'{line_rate * 100:.2f}')
"
}

# 히스토리 파일에 현재 커버리지 추가
update_history() {
    local coverage="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # 히스토리 파일에 추가 (최근 10개만 유지)
    echo "$timestamp $coverage" >> "$HISTORY_FILE"
    tail -n 10 "$HISTORY_FILE" > "${HISTORY_FILE}.tmp"
    mv "${HISTORY_FILE}.tmp" "$HISTORY_FILE"
}

# 최근 N회 연속 threshold 달성 여부 확인
check_consecutive() {
    local threshold="$1"
    local required="$2"

    if [[ ! -f "$HISTORY_FILE" ]]; then
        return 1
    fi

    # 최근 N개 라인 추출
    local recent=$(tail -n "$required" "$HISTORY_FILE" | awk '{print $2}')
    local count=$(echo "$recent" | wc -l)

    if [[ "$count" -lt "$required" ]]; then
        return 1
    fi

    # 모든 항목이 threshold 이상인지 확인 (Python fallback)
    for coverage in $recent; do
        local result=$(python -c "print(1 if float('$coverage') < float('$threshold') else 0)")
        if [[ "$result" == "1" ]]; then
            return 1
        fi
    done

    return 0
}

# 메인 로직
main() {
    echo "🔍 Ratchet Check: 3 consecutive runs ≥${RATCHET_THRESHOLD}% → Gate ${CURRENT_GATE}% → ${TARGET_GATE}%"
    echo ""

    # 1. 현재 커버리지 파싱
    CURRENT_COVERAGE=$(get_coverage "$COVERAGE_XML")
    echo "📊 Current Coverage: ${CURRENT_COVERAGE}%"

    # 2. 히스토리 업데이트
    update_history "$CURRENT_COVERAGE"

    # 3. 히스토리 출력
    echo ""
    echo "📜 Recent Coverage History:"
    if [[ -f "$HISTORY_FILE" ]]; then
        tail -n 5 "$HISTORY_FILE" | awk '{printf "  %s: %6.2f%%\n", $1, $2}'
    else
        echo "  (No history yet)"
    fi

    # 4. 연속 달성 체크
    echo ""
    if check_consecutive "$RATCHET_THRESHOLD" "$CONSECUTIVE_REQUIRED"; then
        echo "✅ RATCHET TRIGGER: 3 consecutive runs ≥${RATCHET_THRESHOLD}%"
        echo "🚀 ACTION REQUIRED: Update gate ${CURRENT_GATE}% → ${TARGET_GATE}%"
        echo ""
        echo "📝 Next Steps:"
        echo "  1. Create PR to update .github/workflows/kis-ci.yml"
        echo "  2. Change coverage threshold: ${CURRENT_GATE} → ${TARGET_GATE}"
        echo "  3. Update COVERAGE_POLICY.md with new gate"
        echo ""

        # 환경변수로 상태 전달 (CI에서 사용 가능)
        echo "RATCHET_TRIGGERED=true" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
        echo "NEW_GATE=${TARGET_GATE}" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true

        exit 0
    else
        local consecutive_count=$(tail -n "$CONSECUTIVE_REQUIRED" "$HISTORY_FILE" 2>/dev/null | \
            awk -v threshold="$RATCHET_THRESHOLD" '$2 >= threshold {count++} END {print count+0}')
        echo "⏳ RATCHET PENDING: ${consecutive_count}/${CONSECUTIVE_REQUIRED} consecutive runs ≥${RATCHET_THRESHOLD}%"
        echo "   Need $(( CONSECUTIVE_REQUIRED - consecutive_count )) more run(s)"

        exit 1
    fi
}

# 실행
main "$@"
