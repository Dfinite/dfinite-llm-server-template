#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# vLLM Server Stop / Status Script (Docker Compose)
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 색상 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════════${NC}
${BLUE}  vLLM Server Stop / Status Script${NC}
${BLUE}═══════════════════════════════════════════════════════════════${NC}

${CYAN}사용법:${NC}
    $0 [명령어]

${CYAN}명령어:${NC}
    stop (기본)     모든 서비스 종료
    llm             LLM 서비스만 종료 (reranker 유지)
    reranker        Reranker 서비스만 종료 (LLM 유지)
    status          현재 상태 확인
    logs [서비스]   로그 보기 (qwen-demo / reranker-women / 미지정=전체)
    restart [서비스] 재시작 (qwen-demo / reranker-women / 미지정=전체)

${CYAN}예시:${NC}
    $0                  # 전체 종료
    $0 llm              # LLM만 종료 (reranker-women 유지)
    $0 reranker         # Reranker만 종료
    $0 status           # 상태 확인
    $0 logs qwen-demo        # LLM 로그
    $0 logs reranker-women   # Reranker 로그
    $0 restart reranker-women # Reranker만 재시작

EOF
}

status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  vLLM Server Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    cd "$SCRIPT_DIR"

    # .env에서 정보 읽기
    local llm_port="8000"
    local reranker_port="8001"
    local model_name="unknown"
    if [[ -f "${SCRIPT_DIR}/.env" ]]; then
        llm_port=$(grep "^HOST_PORT=" "${SCRIPT_DIR}/.env" | cut -d= -f2 | tr -d '"' || echo "8000")
        model_name=$(grep "^MODEL_NAME=" "${SCRIPT_DIR}/.env" | cut -d= -f2 | tr -d '"' || echo "unknown")
        reranker_port=$(grep "^RERANKER_PORT=" "${SCRIPT_DIR}/.env" | cut -d= -f2 | tr -d '"' || echo "8001")
    fi

    # ── LLM 상태 ──
    echo -e "  ${CYAN}[LLM]${NC}"
    local llm_running=$(docker compose ps -q qwen-demo 2>/dev/null)
    if [[ -n "$llm_running" ]] && docker inspect --format '{{.State.Status}}' $llm_running 2>/dev/null | grep -q "running"; then
        echo -e "  ${GREEN}●${NC} Container: running"
        echo -e "    Model: ${model_name}"
        echo -e "    Port:  ${llm_port}"
        if curl -sf "http://localhost:${llm_port}/v1/models" > /dev/null 2>&1; then
            echo -e "  ${GREEN}●${NC} API: responding"
            curl -sf "http://localhost:${llm_port}/v1/models" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('data', []):
    print(f\"    → {m['id']}\")
" 2>/dev/null || true
        else
            echo -e "  ${YELLOW}●${NC} API: loading..."
        fi
    else
        echo -e "  ${RED}●${NC} Container: stopped"
    fi

    echo ""

    # ── Reranker 상태 ──
    echo -e "  ${CYAN}[Reranker]${NC}"
    local rr_running=$(docker compose ps -q reranker-women 2>/dev/null)
    if [[ -n "$rr_running" ]] && docker inspect --format '{{.State.Status}}' $rr_running 2>/dev/null | grep -q "running"; then
        echo -e "  ${GREEN}●${NC} Container: running"
        echo -e "    Port:  ${reranker_port}"
        if curl -sf "http://localhost:${reranker_port}/health" > /dev/null 2>&1; then
            echo -e "  ${GREEN}●${NC} API: responding"
        else
            echo -e "  ${YELLOW}●${NC} API: loading..."
        fi
    else
        echo -e "  ${RED}●${NC} Container: stopped"
    fi

    echo ""

    # ── GPU 상태 ──
    echo -e "  ${CYAN}[GPU]${NC}"
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu \
            --format=csv,noheader | while IFS=, read -r idx name mem_used mem_total util temp; do
            printf "    GPU%s: %s | %s/%s | Util: %s | %s\n" \
                "$(echo $idx | xargs)" "$(echo $name | xargs)" \
                "$(echo $mem_used | xargs)" "$(echo $mem_total | xargs)" \
                "$(echo $util | xargs)" "$(echo $temp | xargs)"
        done
    else
        echo "    (nvidia-smi not available)"
    fi
    echo ""
}

main() {
    local cmd="${1:-stop}"
    local target="${2:-}"

    cd "$SCRIPT_DIR"

    case "$cmd" in
        --help|-h)
            show_help
            ;;
        status)
            status
            ;;
        logs)
            if [[ -n "$target" ]]; then
                docker compose logs --tail 50 -f "$target"
            else
                docker compose logs --tail 50 -f
            fi
            ;;
        restart)
            if [[ -n "$target" ]]; then
                log_info "${target} 재시작..."
                docker compose restart "$target"
            else
                log_info "전체 서비스 재시작..."
                docker compose restart
            fi
            log_info "재시작 완료"
            ;;
        llm)
            log_info "LLM 서비스 종료 (reranker-women은 유지)..."
            docker compose stop qwen-demo
            docker compose rm -f qwen-demo
            log_info "LLM 종료 완료"
            ;;
        reranker)
            log_info "Reranker 서비스 종료 (LLM은 유지)..."
            docker compose stop reranker-women
            docker compose rm -f reranker-women
            log_info "Reranker 종료 완료"
            ;;
        stop|*)
            local running=$(docker compose ps -q 2>/dev/null)
            if [[ -z "$running" ]]; then
                log_info "실행중인 서비스 없음"
            else
                log_info "전체 서비스 종료..."
                docker compose down
                log_info "종료 완료"
            fi
            ;;
    esac
}

main "$@"
