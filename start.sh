#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# vLLM Server Start Script (Docker Compose)
# ═══════════════════════════════════════════════════════════════
# LLM만:        ./start.sh qwen3-32b-awq
# LLM+Reranker: ./start.sh qwen3-32b-awq --with-reranker
# LLM+전체:     ./start.sh qwen3-32b-awq --with-reranker --with-embedding
# Reranker만:   ./start.sh --reranker-only
# Embedding만:  ./start.sh --embedding-only
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/configs"
CHAT_CONFIG_DIR="${CONFIG_DIR}/chat"
RERANKER_CONFIG_DIR="${CONFIG_DIR}/reranker"
EMBEDDING_CONFIG_DIR="${CONFIG_DIR}/embedding"
ENV_FILE="${SCRIPT_DIR}/.env"

# ── 색상 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── PyYAML 확인 ──
ensure_pyyaml() {
    python3 -c "import yaml" 2>/dev/null && return 0
    log_warn "PyYAML 미설치 → 자동 설치중..."
    pip3 install --user --quiet pyyaml 2>/dev/null || pip install --quiet pyyaml
}

# ── 도움말 ──
show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════════${NC}
${BLUE}  vLLM Server Start Script (Docker Compose)${NC}
${BLUE}═══════════════════════════════════════════════════════════════${NC}

${CYAN}사용법:${NC}
    $0 <model_name> [옵션]

${CYAN}명령어:${NC}
    <model_name>        LLM 모델 시작 (configs/chat/ 디렉토리 기준)
    --reranker-only     Reranker 서비스만 시작
    --embedding-only    Embedding 서비스만 시작
    --list, -l          사용 가능한 모델 목록
    --help, -h          이 도움말

${CYAN}옵션:${NC}
    --with-reranker     LLM + Reranker 동시 시작
    --with-embedding    LLM + Embedding 동시 시작
    --port PORT         LLM 호스트 포트 오버라이드
    --tag TAG           vLLM Docker 이미지 태그 (기본: v0.18.0)
    --gpu DEVICES       GPU 디바이스 지정 (예: 0,1)
    --follow, -f        로그 따라가기 (foreground)

${CYAN}예시:${NC}
    $0 qwen3-32b-awq                                    # LLM만 시작
    $0 qwen3-32b-awq --with-reranker                    # LLM + Reranker
    $0 qwen3-32b-awq --with-reranker --with-embedding   # LLM + Reranker + Embedding
    $0 --reranker-only                                   # Reranker만 시작
    $0 --embedding-only                                  # Embedding만 시작
    $0 qwen3.5-35b --port 8002                           # 포트 변경

${CYAN}서비스 개별 관리:${NC}
    docker compose stop qwen-demo             # LLM만 중지
    docker compose stop reranker-women       # Reranker만 중지
    docker compose stop embedding-women      # Embedding만 중지
    docker compose logs -f embedding-women   # Embedding 로그

${CYAN}사용 가능한 Chat (LLM) 모델:${NC}
$(ls -1 "${CHAT_CONFIG_DIR}"/*.yaml 2>/dev/null | xargs -I {} basename {} .yaml | sed 's/^/    /' || echo "    (설정 파일 없음)")

${CYAN}사용 가능한 Reranker 모델:${NC}
$(ls -1 "${RERANKER_CONFIG_DIR}"/*.yaml 2>/dev/null | xargs -I {} basename {} .yaml | sed 's/^/    /' || echo "    (설정 파일 없음)")

${CYAN}사용 가능한 Embedding 모델:${NC}
$(ls -1 "${EMBEDDING_CONFIG_DIR}"/*.yaml 2>/dev/null | xargs -I {} basename {} .yaml | sed 's/^/    /' || echo "    (설정 파일 없음)")

EOF
}

# ── 모델 목록 (configs 디렉토리에서 동적으로 읽기) ──
_list_configs() {
    local dir="$1"
    for config_file in "${dir}"/*.yaml; do
        [[ -f "$config_file" ]] || continue
        local name=$(basename "$config_file" .yaml)
        local desc=$(python3 -c "
import yaml
with open('$config_file') as f:
    cfg = yaml.safe_load(f)
print(cfg.get('model', {}).get('description', ''))
" 2>/dev/null || echo "")
        local path=$(python3 -c "
import yaml
with open('$config_file') as f:
    cfg = yaml.safe_load(f)
print(cfg.get('model', {}).get('path', ''))
" 2>/dev/null || echo "")
        printf "  ${GREEN}%-25s${NC} %s\n" "$name" "$desc"
        printf "  %-25s %s\n" "" "$path"
        echo ""
    done
}

list_models() {
    ensure_pyyaml
    echo ""

    echo -e "${BLUE}사용 가능한 Chat (LLM) 모델:${NC}"
    echo ""
    _list_configs "${CHAT_CONFIG_DIR}"

    echo -e "${BLUE}사용 가능한 Reranker 모델:${NC}"
    echo ""
    _list_configs "${RERANKER_CONFIG_DIR}"

    echo -e "${BLUE}사용 가능한 Embedding 모델:${NC}"
    echo ""
    _list_configs "${EMBEDDING_CONFIG_DIR}"
}

# ── LLM 컨테이너만 확인/교체 ──
check_existing_llm() {
    local running=$(docker compose -f "${SCRIPT_DIR}/docker-compose.yaml" ps -q qwen-demo 2>/dev/null)
    if [[ -n "$running" ]]; then
        local state=$(docker inspect --format '{{.State.Status}}' $running 2>/dev/null || echo "unknown")
        if [[ "$state" == "running" ]]; then
            local current_name=$(docker inspect --format '{{.Name}}' $running 2>/dev/null | sed 's/\///')
            log_warn "기존 LLM 컨테이너 실행중: ${current_name}"
            echo ""
            read -p "  LLM 컨테이너를 교체할까요? (Reranker는 유지됩니다) (y/N): " confirm
            if [[ "$confirm" =~ ^[yY]$ ]]; then
                log_info "LLM 컨테이너 종료중..."
                docker compose -f "${SCRIPT_DIR}/docker-compose.yaml" stop qwen-demo
                docker compose -f "${SCRIPT_DIR}/docker-compose.yaml" rm -f qwen-demo
            else
                log_info "취소되었습니다."
                exit 0
            fi
        fi
    fi
}

# ── .env에 reranker 기본값 추가 ──
append_reranker_defaults() {
    local env_file="$1"
    grep -q "^RERANKER_MODEL=" "$env_file" 2>/dev/null || echo "RERANKER_MODEL=BAAI/bge-reranker-v2-m3" >> "$env_file"
    grep -q "^RERANKER_PORT=" "$env_file" 2>/dev/null || echo "RERANKER_PORT=10072" >> "$env_file"
    grep -q "^RERANKER_TP=" "$env_file" 2>/dev/null || echo "RERANKER_TP=1" >> "$env_file"
    grep -q "^RERANKER_GPU_UTIL=" "$env_file" 2>/dev/null || echo "RERANKER_GPU_UTIL=0.05" >> "$env_file"
    grep -q "^RERANKER_GPU=" "$env_file" 2>/dev/null || echo "RERANKER_GPU=all" >> "$env_file"
}

# ── .env에 embedding 기본값 추가 ──
append_embedding_defaults() {
    local env_file="$1"
    grep -q "^EMBEDDING_MODEL=" "$env_file" 2>/dev/null || echo "EMBEDDING_MODEL=BAAI/bge-m3" >> "$env_file"
    grep -q "^EMBEDDING_PORT=" "$env_file" 2>/dev/null || echo "EMBEDDING_PORT=10073" >> "$env_file"
    grep -q "^EMBEDDING_TP=" "$env_file" 2>/dev/null || echo "EMBEDDING_TP=1" >> "$env_file"
    grep -q "^EMBEDDING_GPU_UTIL=" "$env_file" 2>/dev/null || echo "EMBEDDING_GPU_UTIL=0.10" >> "$env_file"
    grep -q "^EMBEDDING_GPU=" "$env_file" 2>/dev/null || echo "EMBEDDING_GPU=all" >> "$env_file"
    grep -q "^EMBEDDING_MAX_MODEL_LEN=" "$env_file" 2>/dev/null || echo "EMBEDDING_MAX_MODEL_LEN=8192" >> "$env_file"
    grep -q "^EMBEDDING_EXTRA_ARGS=" "$env_file" 2>/dev/null || echo "EMBEDDING_EXTRA_ARGS=" >> "$env_file"
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

        local container_status=$(docker compose -f "${SCRIPT_DIR}/docker-compose.yaml" ps --format json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        c = json.loads(line)
        if c.get('State') == 'exited' or c.get('State') == 'dead':
            print('stopped')
            break
    except: pass
" 2>/dev/null)
        if [[ "$container_status" == "stopped" ]]; then
            echo ""
            log_error "${name} 컨테이너가 시작 중 종료됨"
            log_error "로그 확인: docker compose logs --tail 50"
            return 1
        fi

        sleep 5
        waited=$((waited + 5))
        printf "\r  대기중... %d/%d초  " "$waited" "$max_wait"
    done

    echo ""
    log_warn "${name} 준비 시간 초과 (${max_wait}초)"
    return 1
}

# ── 메인 ──
main() {
    local model_name=""
    local port_override=""
    local image_tag=""
    local gpu_devices=""
    local follow=false
    local with_reranker=false
    local with_embedding=false
    local reranker_only=false
    local embedding_only=false

    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)        show_help; exit 0 ;;
            --list|-l)        list_models; exit 0 ;;
            --with-reranker)  with_reranker=true; shift ;;
            --with-embedding) with_embedding=true; shift ;;
            --reranker-only)  reranker_only=true; shift ;;
            --embedding-only) embedding_only=true; shift ;;
            --port)           port_override="$2"; shift 2 ;;
            --tag)            image_tag="$2"; shift 2 ;;
            --gpu)            gpu_devices="$2"; shift 2 ;;
            --follow|-f)      follow=true; shift ;;
            -*)               log_error "알 수 없는 옵션: $1"; exit 1 ;;
            *)                model_name="$1"; shift ;;
        esac
    done

    # Reranker만 시작
    if [[ "$reranker_only" == true ]]; then
        ensure_pyyaml
        log_info "Reranker 서비스만 시작합니다"

        # 최소 .env 생성 (reranker만 필요한 변수)
        if [[ ! -f "$ENV_FILE" ]]; then
            echo "MODEL_NAME=none" > "$ENV_FILE"
            echo "HOST_PORT=10071" >> "$ENV_FILE"
            echo 'VLLM_CMD_ARGS=--help' >> "$ENV_FILE"
        fi

        local hf_cache="${HF_HOME:-${HOME}/.cache/huggingface}"
        grep -q "^HF_CACHE=" "$ENV_FILE" 2>/dev/null || echo "HF_CACHE=${hf_cache}" >> "$ENV_FILE"
        [[ -n "${HF_TOKEN:-}" ]] && grep -q "^HF_TOKEN=" "$ENV_FILE" 2>/dev/null || echo "HF_TOKEN=${HF_TOKEN:-}" >> "$ENV_FILE"
        [[ -n "$image_tag" ]] && echo "VLLM_IMAGE_TAG=${image_tag}" >> "$ENV_FILE"
        append_reranker_defaults "$ENV_FILE"

        cd "$SCRIPT_DIR"
        docker compose --env-file "$ENV_FILE" up -d reranker-women

        echo ""
        wait_for_service "Reranker" "10072" 180
        echo -e "${GREEN}  Reranker API: http://localhost:10072/v1/score${NC}"
        echo ""
        return 0
    fi

    # Embedding만 시작
    if [[ "$embedding_only" == true ]]; then
        ensure_pyyaml
        log_info "Embedding 서비스만 시작합니다"

        if [[ ! -f "$ENV_FILE" ]]; then
            echo "MODEL_NAME=none" > "$ENV_FILE"
            echo "HOST_PORT=10071" >> "$ENV_FILE"
            echo 'VLLM_CMD_ARGS=--help' >> "$ENV_FILE"
        fi

        local hf_cache="${HF_HOME:-${HOME}/.cache/huggingface}"
        grep -q "^HF_CACHE=" "$ENV_FILE" 2>/dev/null || echo "HF_CACHE=${hf_cache}" >> "$ENV_FILE"
        [[ -n "${HF_TOKEN:-}" ]] && grep -q "^HF_TOKEN=" "$ENV_FILE" 2>/dev/null || echo "HF_TOKEN=${HF_TOKEN:-}" >> "$ENV_FILE"
        [[ -n "$image_tag" ]] && echo "VLLM_IMAGE_TAG=${image_tag}" >> "$ENV_FILE"
        append_reranker_defaults "$ENV_FILE"
        append_embedding_defaults "$ENV_FILE"

        cd "$SCRIPT_DIR"
        docker compose --env-file "$ENV_FILE" up -d embedding-women

        echo ""
        wait_for_service "Embedding" "10073" 180
        echo -e "${GREEN}  Embedding API: http://localhost:10073/v1/embeddings${NC}"
        echo ""
        return 0
    fi

    # LLM 모델명 필수
    if [[ -z "$model_name" ]]; then
        show_help
        exit 1
    fi

    local config_file="${CHAT_CONFIG_DIR}/${model_name}.yaml"
    if [[ ! -f "$config_file" ]]; then
        log_error "설정 파일을 찾을 수 없습니다: ${config_file}"
        list_models
        exit 1
    fi

    ensure_pyyaml

    # 기존 LLM 컨테이너 확인 (reranker는 건드리지 않음)
    check_existing_llm

    # ── Config → .env 변환 ──
    log_info "설정 로드: ${model_name}"
    python3 "${SCRIPT_DIR}/scripts/parse_config.py" "$config_file" "$ENV_FILE"

    # 포트 오버라이드
    if [[ -n "$port_override" ]]; then
        sed -i "s/^HOST_PORT=.*/HOST_PORT=${port_override}/" "$ENV_FILE"
        log_info "포트 오버라이드: ${port_override}"
    fi

    # GPU 디바이스 오버라이드
    if [[ -n "$gpu_devices" ]]; then
        echo "NVIDIA_VISIBLE_DEVICES=${gpu_devices}" >> "$ENV_FILE"
        log_info "GPU 디바이스: ${gpu_devices}"
    fi

    # 이미지 태그 오버라이드
    if [[ -n "$image_tag" ]]; then
        echo "VLLM_IMAGE_TAG=${image_tag}" >> "$ENV_FILE"
        log_info "이미지 태그: ${image_tag}"
    fi

    # HF 설정
    [[ -n "${HF_TOKEN:-}" ]] && echo "HF_TOKEN=${HF_TOKEN}" >> "$ENV_FILE"
    local hf_cache="${HF_HOME:-${HOME}/.cache/huggingface}"
    echo "HF_CACHE=${hf_cache}" >> "$ENV_FILE"

    # Reranker/Embedding 기본값 추가 (.env에 있어야 compose가 에러 안 남)
    append_reranker_defaults "$ENV_FILE"
    append_embedding_defaults "$ENV_FILE"

    # ── 시작할 서비스 결정 ──
    local services="qwen-demo"
    if [[ "$with_reranker" == true ]]; then
        services="$services reranker-women"
    fi
    if [[ "$with_embedding" == true ]]; then
        services="$services embedding-women"
    fi

    local port=$(grep "^HOST_PORT=" "$ENV_FILE" | cut -d= -f2 | tr -d '"')

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  vLLM Server Starting: ${model_name}${NC}"
    echo -e "${BLUE}  LLM Port: ${port}${NC}"
    [[ "$with_reranker" == true ]] && \
    echo -e "${BLUE}  Reranker Port: 10072${NC}"
    [[ "$with_embedding" == true ]] && \
    echo -e "${BLUE}  Embedding Port: 10073${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    cd "$SCRIPT_DIR"

    if [[ "$follow" == true ]]; then
        log_info "Foreground 모드 (Ctrl+C로 종료)"
        docker compose --env-file "$ENV_FILE" up $services
    else
        docker compose --env-file "$ENV_FILE" up -d $services
        echo ""
        log_info "컨테이너 시작됨 (백그라운드)"
        log_info "로그: docker compose logs -f"
        echo ""

        # LLM 준비 대기
        wait_for_service "LLM" "$port" 600

        # Reranker 준비 대기
        if [[ "$with_reranker" == true ]]; then
            wait_for_service "Reranker" "10072" 180
        fi

        # Embedding 준비 대기
        if [[ "$with_embedding" == true ]]; then
            wait_for_service "Embedding" "10073" 180
        fi

        # 결과 출력
        echo ""
        echo -e "${GREEN}  LLM API:         http://localhost:${port}/v1${NC}"
        echo -e "${GREEN}  LLM Health:      http://localhost:${port}/health${NC}"
        if [[ "$with_reranker" == true ]]; then
        echo -e "${GREEN}  Reranker API:    http://localhost:10072/v1/score${NC}"
        fi
        if [[ "$with_embedding" == true ]]; then
        echo -e "${GREEN}  Embedding API:   http://localhost:10073/v1/embeddings${NC}"
        fi
        echo ""
    fi
}

main "$@"
