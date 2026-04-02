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
│   ├── parse_config.py      # Config → .env 변환
│   └── manage_compose.py    # Docker Compose 서비스 동적 관리
├── docker-compose.yaml
├── services.json            # 서비스 레지스트리 (manage_compose.py가 생성)
├── start.sh                 # 서버 시작
├── stop.sh                  # 서버 종료 / 상태 / 로그
├── health_check.sh          # 헬스 체크
└── .env.example
```

## Docker Compose 서비스 관리

`scripts/manage_compose.py`로 docker-compose.yaml의 서비스를 동적으로 추가/삭제합니다.
`services.json` 레지스트리를 기반으로 docker-compose.yaml을 자동 재생성합니다.

### 서비스 추가

```bash
# chat 서비스 추가
./scripts/manage_compose.py add chat qwen3-32b-awq --name my-llm --port 10071

# reranker 추가
./scripts/manage_compose.py add reranker bge-reranker-v2-m3 --name my-reranker --port 10072

# embedding 추가
./scripts/manage_compose.py add embedding bge-m3 --name my-embed --port 10073

# 두 번째 LLM 추가 (다른 이름, 다른 포트)
./scripts/manage_compose.py add chat qwen3.5-35b --name qwen35 --port 10074

# GPU 지정
./scripts/manage_compose.py add chat qwen3-32b-awq --name my-llm --gpu 0,1
```

### 서비스 삭제

```bash
./scripts/manage_compose.py remove my-llm
```

### 서비스 목록

```bash
./scripts/manage_compose.py list
# NAME                      TYPE         CONFIG                    PORT     GPU
# ────────────────────────────────────────────────────────────────────────────────
# my-llm                    chat         qwen3-32b-awq             10071    all
# my-reranker               reranker     bge-reranker-v2-m3        10072    all
# my-embed                  embedding    bge-m3                    10073    all
```

### 초기 설정 (마이그레이션)

기존 구성을 `services.json`으로 등록합니다.

```bash
./scripts/manage_compose.py init
```

### 참고

- `--name` 생략 시 `{type}-{config_name}` 형태로 자동 생성
- `--port` 생략 시 config YAML의 기본 포트 사용, 충돌 시 자동 증가
- docker-compose.yaml은 `manage_compose.py`가 재생성하므로 직접 수정하지 마세요

---

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
