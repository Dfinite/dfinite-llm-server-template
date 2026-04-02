#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# vLLM Server Health Check
# ═══════════════════════════════════════════════════════════════
# services.json에서 등록된 서비스를 자동으로 체크합니다.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${SCRIPT_DIR}/services.json"

GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
NC=$'\033[0m'

WATCH=false
JSON=false
TIMEOUT=5

while [[ $# -gt 0 ]]; do
    case "$1" in
        -w|--watch) WATCH=true; shift ;;
        -j|--json)  JSON=true; shift ;;
        -t|--timeout) TIMEOUT="$2"; shift 2 ;;
        -h|--help)
            echo "사용법: $0 [-w|--watch] [-j|--json] [-t TIMEOUT]"
            exit 0 ;;
        *) shift ;;
    esac
done

if [[ ! -f "$REGISTRY" ]]; then
    echo "ERROR: services.json이 없습니다."
    exit 1
fi

check_service() {
    local port="$1"
    local code=$(curl -sf -o /dev/null -w '%{http_code}' \
        --connect-timeout "$TIMEOUT" --max-time "$TIMEOUT" \
        "http://localhost:${port}/health" 2>/dev/null || echo "000")
    echo "$code"
}

do_check() {
    local ts=$(date '+%Y-%m-%d %H:%M:%S')

    # services.json 파싱
    local services_data
    services_data=$(python3 -c "
import json
with open('$REGISTRY') as f:
    reg = json.load(f)
for name, svc in reg.get('services', {}).items():
    print(f\"{name}|{svc['port']}|{svc['type']}|{svc['config']}\")
" 2>/dev/null)

    if [[ "$JSON" == true ]]; then
        local json_parts=()
        local all_healthy=true
        while IFS='|' read -r name port stype config; do
            local code=$(check_service "$port")
            local healthy=$([[ "$code" == "200" ]] && echo "true" || echo "false")
            [[ "$healthy" == "false" ]] && all_healthy=false
            json_parts+=("\"$name\": {\"type\": \"$stype\", \"config\": \"$config\", \"port\": $port, \"healthy\": $healthy, \"http_code\": $code}")
        done <<< "$services_data"

        echo "{"
        echo "  \"timestamp\": \"$ts\","
        local i=0
        for part in "${json_parts[@]}"; do
            i=$((i + 1))
            if [[ $i -lt ${#json_parts[@]} ]]; then
                echo "  $part,"
            else
                echo "  $part"
            fi
        done
        echo "}"
        return
    fi

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  vLLM Health Check  │  ${ts}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    while IFS='|' read -r name port stype config; do
        local code=$(check_service "$port")
        if [[ "$code" == "200" ]]; then
            echo -e "  ${GREEN}✓${NC} ${name} (${config}): OK  — :${port}"
        elif [[ "$code" == "000" ]]; then
            echo -e "  ${RED}✗${NC} ${name} (${config}): UNREACHABLE  — :${port}"
        else
            echo -e "  ${YELLOW}⚠${NC} ${name} (${config}): HTTP ${code}  — :${port}"
        fi
    done <<< "$services_data"

    echo ""
}

if [[ "$WATCH" == true ]]; then
    while true; do
        clear
        do_check
        echo -e "  ${BLUE}(5초 간격 │ Ctrl+C 종료)${NC}"
        sleep 5
    done
else
    do_check
fi
