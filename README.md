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

### 2. 사전 준비

```bash
# PyYAML (스크립트에 필요)
pip3 install pyyaml

# 실행 권한
chmod +x start.sh stop.sh health_check.sh

# (선택) HuggingFace 토큰
export HF_TOKEN="hf_..."
```

### 3. 서비스 등록

`manage_compose.py`로 서비스를 등록하면 `docker-compose.yaml`이 자동 생성됩니다.

```bash
# LLM 서비스 등록
./scripts/manage_compose.py add chat qwen3-32b-awq --name my-llm --port 10071

# Reranker 등록
./scripts/manage_compose.py add reranker bge-reranker-v2-m3 --name reranker-women --port 10072

# Embedding 등록
./scripts/manage_compose.py add embedding bge-m3 --name embedding-women --port 10073

# VLM 등록
./scripts/manage_compose.py add vlm qwen3.5-27b-vlm --name my-vlm --port 30071

# GPU 지정
./scripts/manage_compose.py add chat qwen3-32b-awq --name my-llm --port 10071 --gpu 0,1
```

- `--name` 생략 시 `{type}-{config_name}` 형태로 자동 생성
- `--port` 생략 시 타입별 기본 포트 사용 (chat/vlm: 10071, reranker: 10072, embedding: 10073), 충돌 시 자동 증가
- `docker-compose.yaml`은 자동 생성되므로 직접 수정하지 마세요

### 4. 서버 시작

```bash
./start.sh                          # 등록된 전체 서비스 시작
./start.sh my-llm                   # 특정 서비스만 시작
./start.sh my-llm reranker-women    # 여러 서비스 시작
./start.sh -f my-llm                # foreground 모드
```

등록된 서비스 목록 확인:

```bash
./start.sh --list
```

### 5. 로그 확인 및 헬스 체크

```bash
# 로그 확인
./stop.sh logs                   # 전체 로그
./stop.sh logs my-llm            # 특정 서비스 로그

# 헬스 체크
./health_check.sh                # 1회 체크
./health_check.sh -w             # 5초 간격 지속 모니터링
./health_check.sh -j             # JSON 출력
```

### 6. 서버 종료 및 관리

```bash
./stop.sh                        # 전체 종료
./stop.sh stop my-llm            # 특정 서비스만 종료
./stop.sh status                 # 컨테이너 상태 + GPU 사용량 확인
./stop.sh restart my-llm         # 특정 서비스 재시작
```

### 7. 서비스 변경

```bash
# 모델 교체: 삭제 후 재등록
./scripts/manage_compose.py remove my-llm
./scripts/manage_compose.py add chat qwen3.5-27b --name my-llm --port 10071

# 서비스 목록 확인
./scripts/manage_compose.py list
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
│   ├── parse_config.py      # Config → vLLM 명령어 변환
│   └── manage_compose.py    # 서비스 등록/삭제, compose 생성
├── docker-compose.yaml      # 자동 생성 (manage_compose.py)
├── services.json            # 서비스 레지스트리 (manage_compose.py)
├── start.sh                 # 서비스 시작
├── stop.sh                  # 서비스 종료 / 상태 / 로그
├── health_check.sh          # 헬스 체크
└── .env.example
```

## Config 구조

Config 파일은 모델 고유 속성만 정의합니다. 포트, GPU 등 배치 설정은 `manage_compose.py add` 시 지정합니다.

```yaml
# configs/chat/qwen3-32b-awq.yaml
model:
  name: "qwen3-32b-awq"
  path: "Qwen/Qwen3-32B-AWQ"
  description: "Qwen3 32B AWQ 양자화 모델"

vllm:
  tensor_parallel_size: 2
  max_model_len: 32768
  gpu_memory_utilization: 0.80
  dtype: "auto"
  reasoning_parser: "qwen3"
  enable_auto_tool_choice: true
  tool_call_parser: "hermes"
  trust_remote_code: true
  enable_prefix_caching: true
  env: {}
  extra_args: []
```

자세한 작성 방법은 [configs/README.md](configs/README.md) 참고.
