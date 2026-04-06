#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# vLLM Server Stop / Status Script
# ═══════════════════════════════════════════════════════════════
# services.json 레지스트리 기반으로 서비스를 관리합니다.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${SCRIPT_DIR}/services.json"

# ── 색상 ──
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

# ── services.json 읽기 ──
get_service_port() {
    local name="$1"
    python3 -c "
import json
with open('$REGISTRY') as f:
    reg = json.load(f)
svc = reg.get('services', {}).get('$name')
if svc:
    print(svc['port'])
" 2>/dev/null
}

get_all_services() {
    [[ ! -f "$REGISTRY" ]] && return
    python3 -c "
import json
with open('$REGISTRY') as f:
    reg = json.load(f)
for name, svc in reg.get('services', {}).items():
    print(f\"{name} {svc['port']} {svc['type']}\")
" 2>/dev/null
}

# ── 상태 확인 ──
status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  vLLM Server Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    cd "$SCRIPT_DIR"

    # 등록된 서비스명 수집
    local registered_names=()

    if [[ ! -f "$REGISTRY" ]]; then
        echo "  등록된 서비스 없음 (services.json 미존재)"
        echo ""
    fi

    while IFS=' ' read -r name port stype; do
        registered_names+=("$name")
        echo -e "  ${CYAN}[${name}]${NC} (${stype}, port ${port})"
        local running=$(docker compose ps -q "$name" 2>/dev/null)
        if [[ -n "$running" ]] && docker inspect --format '{{.State.Status}}' $running 2>/dev/null | grep -q "running"; then
            echo -e "  ${GREEN}●${NC} Container: running"
            if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
                echo -e "  ${GREEN}●${NC} API: responding"
            else
                echo -e "  ${YELLOW}●${NC} API: loading..."
            fi
        else
            echo -e "  ${RED}●${NC} Container: stopped"
        fi
        echo ""
    done < <(get_all_services)

    # ── 미등록 컨테이너 (이전 설정으로 실행 중인 것) ──
    # docker compose ps는 현재 compose 기준이라 이전 컨테이너를 못 찾음
    # docker ps로 vllm- 접두사 컨테이너를 직접 탐색
    local orphans=""
    while read -r cname cstatus; do
        [[ -z "$cname" ]] && continue
        local is_registered=false
        for rname in "${registered_names[@]}"; do
            if [[ "$cname" == "vllm-${rname}" ]]; then
                is_registered=true
                break
            fi
        done
        if [[ "$is_registered" == false ]]; then
            orphans+="${cname} ${cstatus}"$'\n'
        fi
    done < <(docker ps --filter "name=vllm-" --format '{{.Names}} {{.Status}}' 2>/dev/null)

    if [[ -n "$orphans" ]]; then
        echo -e "  ${YELLOW}[미등록 컨테이너]${NC}"
        echo -e "  ${YELLOW}  services.json에 없지만 실행 중인 컨테이너:${NC}"
        while read -r line; do
            [[ -z "$line" ]] && continue
            echo -e "  ${YELLOW}●${NC} ${line}"
        done <<< "$orphans"
        echo -e "  ${YELLOW}  정리: docker stop <컨테이너명> && docker rm <컨테이너명>${NC}"
        echo ""
    fi

    # ── GPU 상태 ──
    echo -e "  ${CYAN}[GPU]${NC}"
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu \
            --format=csv,noheader | while IFS=, read -r idx gname mem_used mem_total util temp; do
            printf "    GPU%s: %s | %s/%s | Util: %s | %s\n" \
                "$(echo $idx | xargs)" "$(echo $gname | xargs)" \
                "$(echo $mem_used | xargs)" "$(echo $mem_total | xargs)" \
                "$(echo $util | xargs)" "$(echo $temp | xargs)"
        done
    else
        echo "    (nvidia-smi not available)"
    fi
    echo ""
}

show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════════${NC}
${BLUE}  vLLM Server Stop / Status Script${NC}
${BLUE}═══════════════════════════════════════════════════════════════${NC}

${CYAN}사용법:${NC}
    $0 [명령어] [서비스명]

${CYAN}명령어:${NC}
    stop (기본)         전체 또는 지정 서비스 종료
    status              현재 상태 확인
    logs [서비스명]     로그 보기
    restart [서비스명]  재시작

${CYAN}예시:${NC}
    $0                      # 전체 종료
    $0 stop my-llm          # 특정 서비스만 종료
    $0 status               # 상태 확인
    $0 logs my-llm          # 특정 서비스 로그
    $0 restart my-llm       # 특정 서비스 재시작

EOF
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
        stop|*)
            if [[ -n "$target" ]]; then
                log_info "${target} 서비스 종료..."
                docker compose stop "$target"
                docker compose rm -f "$target"
                log_info "${target} 종료 완료"
            else
                local running=$(docker compose ps -q 2>/dev/null)
                if [[ -z "$running" ]]; then
                    log_info "실행중인 서비스 없음"
                else
                    log_info "전체 서비스 종료..."
                    docker compose down --remove-orphans
                    log_info "종료 완료"
                fi
            fi
            ;;
    esac
}

main "$@"
