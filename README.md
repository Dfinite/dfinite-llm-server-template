# dfinite-llm-server-template

vLLM + Docker Compose 기반 LLM 서빙 템플릿.

## 배포 순서

### 1. 레포 클론 및 브랜치 설정

```bash
git clone git@github.com:Dfinite/dfinite-llm-server-template.git
cd dfinite-llm-server-template
```

- 새 GPU 서버를 추가하는 경우: `git checkout -b feat/{새gpu서버명}` (예: `feat/a6000`, `feat/l40s`)
- 기존 서버에서 작업하는 경우: 해당 브랜치로 이동 `git checkout feat/{서버명}`

### 2. docker-compose.yaml 서비스 구성

필요한 서비스를 `docker-compose.yaml`에 정의합니다.

| 서비스 유형 | 서비스명 규칙 | 예시 |
|-------------|---------------|------|
| Chat (LLM) | `{모델대표명}-{서비스명}` | `qwen-demo`, `qwen-women` |
| Reranker | `{모델대표명}-{서비스명}` | `reranker-women` |
| Embedding | `{모델대표명}-{서비스명}` | `embedding-women` |
| VLM | `{모델대표명}-{서비스명}` | `qwen-vlm-women` |

포트는 서비스별로 겹치지 않게 지정합니다.

### 3. 모델 config 작성

`configs/` 하위 디렉토리에 모델별 YAML 설정 파일을 작성합니다.

```
configs/
  chat/         # Chat (LLM) 모델
  vlm/          # Vision Language 모델
  reranker/     # Reranker 모델
  embedding/    # Embedding 모델
```

작성 방법은 [configs/README.md](configs/README.md) 참고. 기존 파일을 복사 후 수정하는 것이 가장 빠릅니다.

### 4. 사전 준비

```bash
# PyYAML (parse_config.py에 필요)
pip3 install pyyaml

# 실행 권한
chmod +x start.sh stop.sh health_check.sh

# (선택) HuggingFace 토큰
export HF_TOKEN="hf_..."
```

### 5. 서버 시작

```bash
./start.sh <model_name>                                     # LLM만 시작
./start.sh <model_name> --with-reranker                     # LLM + Reranker
./start.sh <model_name> --with-reranker --with-embedding    # LLM + Reranker + Embedding
./start.sh --reranker-only                                   # Reranker만
./start.sh --embedding-only                                  # Embedding만
```

사용 가능한 모델 목록 확인:

```bash
./start.sh --list
```

### 6. 로그 확인 및 헬스 체크

```bash
# 로그 확인
./stop.sh logs                   # 전체 로그
./stop.sh logs {서비스명}        # 특정 서비스 로그

# 헬스 체크
./health_check.sh                # 1회 체크
./health_check.sh -w             # 5초 간격 지속 모니터링
./health_check.sh -j             # JSON 출력
```

### 7. 서버 종료 및 관리

```bash
./stop.sh                        # 전체 종료
./stop.sh llm                    # LLM만 종료 (Reranker/Embedding 유지)
./stop.sh reranker               # Reranker만 종료
./stop.sh embedding              # Embedding만 종료
./stop.sh status                 # 컨테이너 상태 + GPU 사용량 확인
./stop.sh restart {서비스명}     # 특정 서비스 재시작
```

---

## 디렉토리 구조

```
├── configs/
│   ├── chat/                # Chat (LLM) 모델 설정
│   ├── vlm/                 # VLM 모델 설정
│   ├── reranker/            # Reranker 모델 설정
│   ├── embedding/           # Embedding 모델 설정
│   └── README.md            # Config 작성 가이드
├── scripts/
│   └── parse_config.py      # Config → .env 변환
├── docker-compose.yaml
├── start.sh                 # 서버 시작
├── stop.sh                  # 서버 종료 / 상태 / 로그
├── health_check.sh          # 헬스 체크
└── .env.example
```

## start.sh 옵션

```bash
./start.sh <model_name> [옵션]
```

| 옵션 | 설명 |
|------|------|
| `<model_name>` | configs/chat/ 또는 configs/vlm/ 의 모델명 |
| `--with-reranker` | LLM + Reranker 동시 시작 |
| `--with-embedding` | LLM + Embedding 동시 시작 |
| `--reranker-only` | Reranker 서비스만 시작 |
| `--embedding-only` | Embedding 서비스만 시작 |
| `--port PORT` | LLM 호스트 포트 오버라이드 |
| `--tag TAG` | vLLM Docker 이미지 태그 지정 |
| `--gpu DEVICES` | GPU 디바이스 지정 (예: `0,1`) |
| `--follow, -f` | 로그 따라가기 (foreground) |
| `--list, -l` | 사용 가능한 모델 목록 |

```bash
# 예시
./start.sh qwen3-32b-awq                                    # LLM만 시작
./start.sh qwen3-32b-awq --with-reranker                    # LLM + Reranker
./start.sh qwen3-32b-awq --with-reranker --with-embedding   # LLM + Reranker + Embedding
./start.sh --reranker-only                                   # Reranker만
./start.sh --embedding-only                                  # Embedding만
./start.sh qwen3.5-35b --port 8002                           # 포트 변경
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
| `embedding` | Embedding만 종료 |
| `status` | 컨테이너 상태 + GPU 사용량 확인 |
| `logs [서비스]` | 로그 보기 (`qwen-woman` / `reranker-women` / `embedding-women` / 전체) |
| `restart [서비스]` | 서비스 재시작 |

```bash
# 예시
./stop.sh                        # 전체 종료
./stop.sh llm                    # LLM만 종료
./stop.sh status                 # 상태 확인
./stop.sh embedding              # Embedding만 종료
./stop.sh logs embedding-women   # Embedding 로그
./stop.sh restart reranker-women # Reranker 재시작
```

### health_check.sh

LLM, Reranker, Embedding의 헬스 상태를 확인합니다.

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

### Embedding 모델 (EMBEDDING_MODEL 환경변수로 선택)

| 모델 | Params | Dim | VRAM |
|------|--------|-----|------|
| `BAAI/bge-m3` | 568M | 1024 | ~1.1GB |
| `dragonkue/BGE-m3-ko` | 568M | 1024 | ~1.1GB |
| `Qwen/Qwen3-Embedding-0.6B` | 0.6B | 1024 | ~1.2GB |
| `Qwen/Qwen3-Embedding-4B` | 4B | 2560 | ~8GB |
| `Qwen/Qwen3-Embedding-8B` | 8B | 4096 | ~16GB |

## 새 모델 추가

1. `configs/`에 YAML 파일 생성 (기존 파일 복사 후 수정)
2. `model.path` = HuggingFace 모델 경로
3. `vllm.*` = 서빙 파라미터 (tp, context length, memory 등)
4. `./start.sh <새_모델_이름>`
