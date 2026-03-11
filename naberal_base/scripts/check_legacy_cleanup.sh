#!/usr/bin/env bash
# 레거시 코드 정리 상태 체크
# Usage: ./scripts/check_legacy_cleanup.sh

set -euo pipefail

GRACE_DEADLINE="2025-11-04"
LEGACY_PATHS=(
    "old_engine"
    "src/kis_estimator_core/old_engine"
)

# 날짜 비교 (YYYY-MM-DD 형식)
is_past_deadline() {
    local deadline="$1"
    local today=$(date -u +"%Y-%m-%d")

    # 날짜를 초 단위로 변환하여 비교
    local deadline_sec=$(date -d "$deadline" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$deadline" +%s)
    local today_sec=$(date -d "$today" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$today" +%s)

    [[ "$today_sec" -gt "$deadline_sec" ]]
}

# 레거시 경로 존재 체크
check_legacy_paths() {
    local found_legacy=false
    local legacy_files=()

    for path in "${LEGACY_PATHS[@]}"; do
        if [[ -e "$path" ]]; then
            found_legacy=true
            # 파일/디렉토리 수 카운트
            if [[ -d "$path" ]]; then
                local count=$(find "$path" -type f 2>/dev/null | wc -l)
                legacy_files+=("$path/ (${count} files)")
            else
                legacy_files+=("$path (file)")
            fi
        fi
    done

    echo "$found_legacy"
    if [[ "$found_legacy" == "true" ]]; then
        printf '%s\n' "${legacy_files[@]}"
    fi
}

# 메인 로직
main() {
    echo "🗑️  Legacy Cleanup Status Check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📅 Grace Period Deadline: $GRACE_DEADLINE"
    echo "📆 Today: $(date -u +"%Y-%m-%d")"
    echo ""

    # 레거시 경로 체크
    local has_legacy
    read -r has_legacy < <(check_legacy_paths)

    if [[ "$has_legacy" == "false" ]]; then
        echo "✅ CLEAN: No legacy code found"
        echo ""
        echo "All legacy paths have been removed:"
        for path in "${LEGACY_PATHS[@]}"; do
            echo "  - $path (removed)"
        done
        exit 0
    fi

    # 레거시 코드 발견
    echo "⚠️  Legacy Code Found:"
    check_legacy_paths | tail -n +2 | while read -r line; do
        echo "  - $line"
    done
    echo ""

    # 유예 기간 체크
    if is_past_deadline "$GRACE_DEADLINE"; then
        echo "❌ GRACE PERIOD EXPIRED"
        echo ""
        echo "The grace period ended on $GRACE_DEADLINE."
        echo "Legacy code must be removed immediately."
        echo ""
        echo "📝 Action Required:"
        echo "  1. Delete or archive legacy paths:"
        for path in "${LEGACY_PATHS[@]}"; do
            if [[ -e "$path" ]]; then
                echo "     rm -rf $path"
            fi
        done
        echo "  2. Verify SSOT migration is complete"
        echo "  3. Run full test suite to ensure no regressions"
        echo ""
        exit 1
    else
        # 유예 기간 내
        local days_remaining=$(( ($(date -d "$GRACE_DEADLINE" +%s) - $(date -u +%s)) / 86400 ))
        echo "⏳ GRACE PERIOD ACTIVE"
        echo ""
        echo "Legacy code is allowed until $GRACE_DEADLINE."
        echo "Days remaining: $days_remaining"
        echo ""
        echo "⚠️  WARNING: This is a temporary state."
        echo ""
        echo "📝 Migration Plan (from SSOT_MIGRATION.md):"
        echo "  1. Verify all active code uses core/ssot/constants/registry.py"
        echo "  2. Review old_engine/** for any missing migrations"
        echo "  3. Archive or delete legacy code before deadline"
        echo "  4. Update .gitignore if needed"
        echo ""

        # 경고 레벨 설정 (마지막 7일은 더 강한 경고)
        if [[ "$days_remaining" -le 7 ]]; then
            echo "🚨 URGENT: Only $days_remaining days left!"
            exit 2  # Warning exit code
        else
            exit 0  # OK for now
        fi
    fi
}

# 실행
main "$@"
