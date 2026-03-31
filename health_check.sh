#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# vLLM Server Health Check (LLM + Reranker + Embedding)
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'

# .env에서 읽기
LLM_PORT=10071
RERANKER_PORT=10072
EMBEDDING_PORT=10073
MODEL_NAME="unknown"
RERANKER_MODEL="unknown"
EMBEDDING_MODEL="unknown"
if [[ -f "$ENV_FILE" ]]; then
    LLM_PORT=$(grep "^HOST_PORT=" "$ENV_FILE" | cut -d= -f2 | tr -d '"' || echo "10071")
    RERANKER_PORT=$(grep "^RERANKER_PORT=" "$ENV_FILE" | cut -d= -f2 | tr -d '"' || echo "10072")
    EMBEDDING_PORT=$(grep "^EMBEDDING_PORT=" "$ENV_FILE" | cut -d= -f2 | tr -d '"' || echo "10073")
    MODEL_NAME=$(grep "^MODEL_NAME=" "$ENV_FILE" | cut -d= -f2 | tr -d '"' || echo "unknown")
    RERANKER_MODEL=$(grep "^RERANKER_MODEL=" "$ENV_FILE" | cut -d= -f2 | tr -d '"' || echo "unknown")
    EMBEDDING_MODEL=$(grep "^EMBEDDING_MODEL=" "$ENV_FILE" | cut -d= -f2 | tr -d '"' || echo "unknown")
fi

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

check_service() {
    local name="$1"
    local port="$2"
    local code=$(curl -sf -o /dev/null -w '%{http_code}' \
        --connect-timeout "$TIMEOUT" --max-time "$TIMEOUT" \
        "http://localhost:${port}/health" 2>/dev/null || echo "000")
    echo "$code"
}

do_check() {
    local ts=$(date '+%Y-%m-%d %H:%M:%S')

    local llm_code=$(check_service "LLM" "$LLM_PORT")
    local rr_code=$(check_service "Reranker" "$RERANKER_PORT")
    local emb_code=$(check_service "Embedding" "$EMBEDDING_PORT")

    if [[ "$JSON" == true ]]; then
        python3 -c "
import json
result = {
    'timestamp': '$ts',
    'llm': {
        'model': '$MODEL_NAME', 'port': $LLM_PORT,
        'healthy': $llm_code == 200, 'http_code': $llm_code
    },
    'reranker': {
        'model': '$RERANKER_MODEL', 'port': $RERANKER_PORT,
        'healthy': $rr_code == 200, 'http_code': $rr_code
    },
    'embedding': {
        'model': '$EMBEDDING_MODEL', 'port': $EMBEDDING_PORT,
        'healthy': $emb_code == 200, 'http_code': $emb_code
    },
    'all_healthy': ($llm_code == 200) and ($rr_code == 200) and ($emb_code == 200)
}
print(json.dumps(result, indent=2, ensure_ascii=False))
" 2>/dev/null
        return
    fi

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  vLLM Health Check  │  ${ts}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    # LLM
    if [[ "$llm_code" == "200" ]]; then
        echo -e "  ${GREEN}✓${NC} LLM (${MODEL_NAME}): OK  — :${LLM_PORT}"
    elif [[ "$llm_code" == "000" ]]; then
        echo -e "  ${RED}✗${NC} LLM (${MODEL_NAME}): UNREACHABLE  — :${LLM_PORT}"
    else
        echo -e "  ${YELLOW}⚠${NC} LLM (${MODEL_NAME}): HTTP ${llm_code}  — :${LLM_PORT}"
    fi

    # Reranker
    if [[ "$rr_code" == "200" ]]; then
        echo -e "  ${GREEN}✓${NC} Reranker: OK  — :${RERANKER_PORT}"
    elif [[ "$rr_code" == "000" ]]; then
        echo -e "  ${RED}✗${NC} Reranker: UNREACHABLE  — :${RERANKER_PORT}"
    else
        echo -e "  ${YELLOW}⚠${NC} Reranker: HTTP ${rr_code}  — :${RERANKER_PORT}"
    fi

    # Embedding
    if [[ "$emb_code" == "200" ]]; then
        echo -e "  ${GREEN}✓${NC} Embedding: OK  — :${EMBEDDING_PORT}"
    elif [[ "$emb_code" == "000" ]]; then
        echo -e "  ${RED}✗${NC} Embedding: UNREACHABLE  — :${EMBEDDING_PORT}"
    else
        echo -e "  ${YELLOW}⚠${NC} Embedding: HTTP ${emb_code}  — :${EMBEDDING_PORT}"
    fi

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
