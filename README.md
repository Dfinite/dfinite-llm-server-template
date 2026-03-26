# dfinite-a6000-model

A6000 48GB x 2 환경에서 vLLM + Docker Compose 기반 모델 서빙.

## 디렉토리 구조

```
├── configs/                 # 모델별 YAML 설정
├── scripts/
│   └── parse_config.py      # Config → .env 변환
├── docker-compose.yaml
├── start.sh                 # 서버 시작
├── stop.sh                  # 서버 종료 / 상태 / 로그
├── health_check.sh          # 헬스 체크
└── .env.example
```

## 사전 준비

```bash
# PyYAML (parse_config.py에 필요)
pip3 install pyyaml

# 실행 권한
chmod +x start.sh stop.sh health_check.sh

# (선택) HuggingFace 토큰
export HF_TOKEN="hf_..."
```

## 스크립트 설명

### start.sh

모델 서버를 시작합니다. `configs/` 디렉토리의 YAML 설정을 읽어 `.env`를 자동 생성하고 Docker Compose로 컨테이너를 띄웁니다.

```bash
./start.sh <model_name> [옵션]
```

| 옵션 | 설명 |
|------|------|
| `<model_name>` | configs/ 디렉토리의 모델명 (예: `qwen3-32b-awq`) |
| `--with-reranker` | LLM + Reranker 동시 시작 |
| `--reranker-only` | Reranker 서비스만 시작 |
| `--port PORT` | LLM 호스트 포트 오버라이드 |
| `--tag TAG` | vLLM Docker 이미지 태그 지정 |
| `--gpu DEVICES` | GPU 디바이스 지정 (예: `0,1`) |
| `--follow, -f` | 로그 따라가기 (foreground) |
| `--list, -l` | 사용 가능한 모델 목록 |

```bash
# 예시
./start.sh qwen3-32b-awq                    # LLM만 시작
./start.sh qwen3-32b-awq --with-reranker    # LLM + Reranker
./start.sh --reranker-only                   # Reranker만
./start.sh qwen3.5-35b --port 8002          # 포트 변경
./start.sh qwen3.5-35b --tag nightly        # nightly 이미지
```

### stop.sh

서비스 종료, 상태 확인, 로그, 재시작을 처리합니다.

```bash
./stop.sh [명령어] [서비스]
```

| 명령어 | 설명 |
|--------|------|
| `stop` (기본) | 모든 서비스 종료 |
| `llm` | LLM만 종료 (Reranker 유지) |
| `reranker` | Reranker만 종료 (LLM 유지) |
| `status` | 컨테이너 상태 + GPU 사용량 확인 |
| `logs [서비스]` | 로그 보기 (`qwen-demo` / `reranker-women` / 전체) |
| `restart [서비스]` | 서비스 재시작 |

```bash
# 예시
./stop.sh                        # 전체 종료
./stop.sh llm                    # LLM만 종료
./stop.sh status                 # 상태 확인
./stop.sh logs qwen-demo         # LLM 로그
./stop.sh restart reranker-women # Reranker 재시작
```

### health_check.sh

LLM과 Reranker의 헬스 상태를 확인합니다.

```bash
./health_check.sh [옵션]
```

| 옵션 | 설명 |
|------|------|
| `-w, --watch` | 5초 간격으로 지속 모니터링 |
| `-j, --json` | JSON 형식 출력 |
| `-t, --timeout` | HTTP 타임아웃 (초, 기본 5) |

```bash
# 예시
./health_check.sh           # 1회 체크
./health_check.sh -w        # 지속 모니터링
./health_check.sh -j        # JSON 출력 (스크립트 연동용)
```

## 지원 모델

| Config | 모델 | 유형 | VRAM |
|--------|------|------|------|
| `qwen3-32b-awq` | Qwen3-32B-AWQ | Dense AWQ | ~18GB |
| `qwen3.5-35b` | Qwen3.5-35B-A3B-GPTQ-Int4 | MoE GPTQ | ~20GB |
| `qwen3.5-27b` | Qwen3.5-27B | Dense BF16 | ~54GB |
| `nemotron-nano` | Nemotron-3-Nano-30B | MoE BF16 | ~60GB |
| `qwen3-30b-thinking` | Qwen3-30B-A3B-Thinking | MoE BF16 | ~60GB |

## 새 모델 추가

1. `configs/`에 YAML 파일 생성 (기존 파일 복사 후 수정)
2. `model.path` = HuggingFace 모델 경로
3. `vllm.*` = 서빙 파라미터 (tp, context length, memory 등)
4. `./start.sh <새_모델_이름>`
