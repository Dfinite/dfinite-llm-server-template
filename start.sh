#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# vLLM Server Start Script
# ═══════════════════════════════════════════════════════════════
# services.json 레지스트리 기반으로 서비스를 시작합니다.
#
# 전체 시작:     ./start.sh
# 특정 서비스:   ./start.sh my-llm reranker-women
# 서비스 목록:   ./start.sh --list
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${SCRIPT_DIR}/services.json"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yaml"

# ── 색상 ──
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── 사전 확인 ──
check_prerequisites() {
    if [[ ! -f "$REGISTRY" ]]; then
        log_error "services.json이 없습니다."
        echo "  먼저 서비스를 등록하세요:"
        echo "    ./scripts/manage_compose.py add chat qwen3-32b-awq --name my-llm"
        exit 1
    fi
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "docker-compose.yaml이 없습니다."
        echo "  manage_compose.py로 서비스를 등록하면 자동 생성됩니다."
        exit 1
    fi
}

# ── services.json에서 정보 읽기 ──
list_services() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  등록된 서비스${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    python3 -c "
import json
with open('$REGISTRY') as f:
    reg = json.load(f)
if not reg.get('services'):
    print('  (등록된 서비스 없음)')
else:
    print(f\"  {'NAME':<25} {'TYPE':<12} {'CONFIG':<25} {'PORT':<8} {'GPU'}\")
    print('  ' + '─' * 78)
    for name, svc in reg['services'].items():
        print(f\"  {name:<25} {svc['type']:<12} {svc['config']:<25} {svc['port']:<8} {svc.get('gpu', 'all')}\")
"
    echo ""
}

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

get_all_service_names() {
    python3 -c "
import json
with open('$REGISTRY') as f:
    reg = json.load(f)
for name in reg.get('services', {}):
    print(name)
" 2>/dev/null
}

# ── 서버 준비 대기 ──
wait_for_service() {
    local name="$1"
    local port="$2"
    local max_wait="${3:-600}"
    local waited=0

    log_info "${name} 준비 대기중... (포트: ${port})"

    while [[ $waited -lt $max_wait ]]; do
        if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
            echo ""
            log_info "${name} 준비 완료!"
            return 0
        fi

        sleep 5
        waited=$((waited + 5))
        printf "\r  대기중... %d/%d초  " "$waited" "$max_wait"
    done

    echo ""
    log_warn "${name} 준비 시간 초과 (${max_wait}초)"
    return 1
}

# ── 도움말 ──
show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════════${NC}
${BLUE}  vLLM Server Start Script${NC}
${BLUE}═══════════════════════════════════════════════════════════════${NC}

${CYAN}사용법:${NC}
    $0 [서비스명...]                등록된 서비스 시작 (전체 또는 지정)
    $0 --list, -l                   등록된 서비스 목록
    $0 --follow, -f [서비스...]     foreground 모드
    $0 --with-monitoring            모니터링 스택 함께 기동
    $0 --help, -h                   이 도움말

${CYAN}예시:${NC}
    $0                              # 전체 시작
    $0 my-llm                       # 특정 서비스만 시작
    $0 my-llm reranker-women        # 여러 서비스 시작
    $0 -f my-llm                    # foreground 모드
    $0 --with-monitoring            # vLLM + 모니터링 함께 시작

${CYAN}서비스 관리:${NC}
    ./scripts/manage_compose.py add <type> <config> --name <name> --port <port>
    ./scripts/manage_compose.py remove <name>
    ./scripts/manage_compose.py list

EOF
}

# ── 메인 ──
main() {
    local follow=false
    local with_monitoring=false
    local services=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)            show_help; exit 0 ;;
            --list|-l)            check_prerequisites; list_services; exit 0 ;;
            --follow|-f)          follow=true; shift ;;
            --with-monitoring)    with_monitoring=true; shift ;;
            -*)                   log_error "알 수 없는 옵션: $1"; exit 1 ;;
            *)                    services+=("$1"); shift ;;
        esac
    done

    check_prerequisites

    # 서비스 미지정 시 전체
    if [[ ${#services[@]} -eq 0 ]]; then
        while IFS= read -r name; do
            services+=("$name")
        done < <(get_all_service_names)
    fi

    if [[ ${#services[@]} -eq 0 ]]; then
        log_error "시작할 서비스가 없습니다."
        echo "  먼저 서비스를 등록하세요:"
        echo "    ./scripts/manage_compose.py add chat qwen3-32b-awq --name my-llm"
        exit 1
    fi

    # HF 캐시 환경변수 (compose에서 필요)
    export HF_CACHE="${HF_HOME:-${HOME}/.cache/huggingface}"

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  vLLM Server Starting${NC}"
    for svc in "${services[@]}"; do
        local port=$(get_service_port "$svc")
        echo -e "${BLUE}  ${svc}: port ${port}${NC}"
    done
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    cd "$SCRIPT_DIR"

    if [[ "$follow" == true ]]; then
        log_info "Foreground 모드 (Ctrl+C로 종료)"
        docker compose up --remove-orphans "${services[@]}"
    else
        docker compose up -d --remove-orphans "${services[@]}"
        echo ""
        log_info "컨테이너 시작됨 (백그라운드)"
        log_info "로그: docker compose logs -f"
        echo ""

        # 헬스체크 대기
        for svc in "${services[@]}"; do
            local port=$(get_service_port "$svc")
            if [[ -n "$port" ]]; then
                wait_for_service "$svc" "$port" 600
            fi
        done

        # 결과 출력
        echo ""
        for svc in "${services[@]}"; do
            local port=$(get_service_port "$svc")
            echo -e "${GREEN}  ${svc}: http://localhost:${port}${NC}"
        done
        echo ""
    fi

    # 모니터링 스택 기동
    if [[ "$with_monitoring" == true ]]; then
        log_info "모니터링 스택 기동 중..."
        if command -v nvidia-smi &> /dev/null; then
            docker compose -f "$SCRIPT_DIR/monitoring/docker-compose.yml" --profile gpu up -d
        else
            docker compose -f "$SCRIPT_DIR/monitoring/docker-compose.yml" up -d
        fi
        log_info "Grafana: http://localhost:3000"
    fi
}

main "$@"
