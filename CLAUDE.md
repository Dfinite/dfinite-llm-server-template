# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

vLLM + Docker Compose 기반 LLM 서빙 템플릿. `services.json` 레지스트리에 서비스를 등록하면 `docker-compose.yaml`이 자동 생성되는 구조다. `monitoring/` 디렉터리는 GPU·vLLM 메트릭 + 컨테이너 로그 수집을 위한 별도 모니터링 스택이다.

## 주요 명령어

```bash
# 의존성
pip3 install pyyaml

# 서비스 관리
./scripts/manage_compose.py add chat qwen3-32b-awq --name my-llm --port 10071 --gpu 0,1
./scripts/manage_compose.py remove my-llm
./scripts/manage_compose.py list

# vLLM 서버 기동/종료
./start.sh                   # 전체 서비스
./start.sh my-llm            # 특정 서비스
./stop.sh                    # 전체 종료
./stop.sh status             # 상태 + GPU 사용량
./health_check.sh -w         # 5초 간격 지속 모니터링

# 모니터링 스택 (monitoring/ 에서)
cd monitoring
docker compose --profile gpu up -d   # GPU 서버
docker compose up -d                 # GPU 없는 환경

# 모니터링 대시보드 재생성
cd monitoring && make assets
```

## 아키텍처

### 서비스 등록 흐름

```
configs/{type}/{name}.yaml
        ↓  parse_config.py (YAML → vLLM CLI args)
        ↓  manage_compose.py add
services.json (레지스트리) + docker-compose.yaml (자동 생성)
        ↓
start.sh → docker compose up
```

- `docker-compose.yaml`은 `manage_compose.py`가 생성하므로 **직접 수정 금지**
- `services.json`이 source of truth: 서비스명·타입·포트·GPU 매핑을 보관
- `parse_config.py`의 `parse_config(config_path, port)` 함수가 YAML → vLLM 명령어 변환 담당
- config 파일에 포트 없음 — 포트는 `manage_compose.py add --port` 로 배치 시 결정

### Config 구조

```yaml
model:
  name: "모델명"
  path: "HuggingFace/모델경로"
vllm:
  tensor_parallel_size: 2
  runner: pooling        # reranker/embedding만 (chat은 생략)
  env: {}                # 컨테이너 환경변수
  extra_args: []         # vllm serve에 그대로 전달
```

### 모니터링 스택

```
vLLM(:포트) ─scrape→ Alloy(:12345) ─remote_write→ Prometheus(:9090) → Grafana(:3000)
dcgm-exporter(:9400) ─scrape→ Alloy
Docker logs ─push→ Loki(:3100) → Grafana
```

- `monitoring/alloy/config.alloy`: vLLM 타깃이 `172.17.0.1:<port>`로 하드코딩됨 — `services.json`의 실제 포트와 **수동으로 동기화 필요**
- `monitoring/docker-compose.yml`은 메인 프로젝트 compose와 **독립 스택** (네트워크 분리)
- Grafana 대시보드 JSON은 `monitoring/scripts/build_grafana_*.py`로 생성, `make assets`로 전체 재생성

### 서비스 타입별 기본 포트

| 타입 | 기본 포트 |
|------|-----------|
| chat / vlm | 10071 |
| reranker | 10072 |
| embedding | 10073 |

포트 충돌 시 자동 증가 (10071 → 10072 → …)

## 주요 파일

| 파일 | 역할 |
|------|------|
| `services.json` | 서비스 레지스트리 (manage_compose.py가 관리) |
| `docker-compose.yaml` | 자동 생성 — 직접 수정 금지 |
| `scripts/manage_compose.py` | 서비스 등록/삭제, compose 재생성 |
| `scripts/parse_config.py` | YAML config → vLLM CLI args 변환 |
| `monitoring/alloy/config.alloy` | Alloy 수집 파이프라인 (vLLM 타깃 포트 수동 관리) |
| `monitoring/docker-compose.yml` | 모니터링 스택 (healthcheck 포함) |
