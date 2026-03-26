# vLLM API Server

vLLM + Docker Compose 기반 LLM/Reranker 모델 서빙 서버.

YAML 설정으로 모델 관리, vLLM 빌트인 OpenAI-compatible API 사용. LLM과 Reranker를 독립적으로 운영합니다.

## 환경

- **GPU**: A6000 48GB × 2
- **서빙 엔진**: vLLM v0.17.1 (Docker)
- **LLM API**: OpenAI-compatible (`/v1/chat/completions`)
- **Reranker API**: vLLM score (`/v1/score`)
- **Python**: 3.12+ (스크립트용)
- **패키지 관리**: [uv](https://docs.astral.sh/uv/) 권장 (vLLM 공식 추천)

## vLLM 버전

| 태그 | 버전 | 용도 |
|------|------|------|
| `v0.17.1` (기본) | 2026-03-11 | 최신 안정 릴리스 |
| `v0.18.0` | PyPI 최신 | gRPC, nested YAML config 등 |
| `nightly` | 매일 빌드 | Qwen3.5 등 신규 모델 지원 시 |

```bash
# 기본 (v0.17.1)
./start.sh qwen3-32b-awq

# 특정 버전
./start.sh qwen3.5-35b --tag v0.18.0

# nightly (신규 모델 아키텍처 필요 시)
./start.sh qwen3.5-35b --tag nightly
```

> ⚠️ Docker Hub에 태그가 늦게 올라오는 경우가 있습니다. `latest`보다 명시적 버전 태그를 권장합니다.

## 아키텍처

```
docker-compose.yaml
├── vllm (LLM)       ← 모델 교체 가능, tp=2, 포트 8000
└── reranker          ← 항상 실행, tp=1, 포트 8001
```

## 디렉토리 구조

```
vllm-api-server/
├── configs/                        # 모델별 설정
│   ├── qwen3-32b-awq.yaml
│   ├── qwen3.5-35b.yaml
│   ├── qwen3.5-27b.yaml
│   ├── nemotron-nano.yaml
│   ├── qwen3-30b-thinking.yaml
│   └── reranker.yaml               # Reranker 참고용
├── scripts/
│   └── parse_config.py              # Config → .env 변환
├── docker-compose.yaml              # LLM + Reranker 서비스 정의
├── start.sh
├── stop.sh
├── health_check.sh
├── .env.example
└── README.md
```

## 사전 준비

```bash
# 1. Docker + NVIDIA Container Toolkit
# (이미 설치되어 있다고 가정)

# 2. Python 3.12+ (스크립트용)
# uv 설치 (vLLM 공식 권장 패키지 관리자)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. PyYAML (parse_config.py에 필요)
uv pip install pyyaml
# 또는 시스템 pip: pip3 install pyyaml

# 4. 실행 권한
chmod +x start.sh stop.sh health_check.sh

# 5. (선택) HuggingFace 토큰
export HF_TOKEN="hf_..."
```

## 빠른 시작

```bash
# LLM만 시작
./start.sh qwen3-32b-awq

# LLM + Reranker 동시 시작
./start.sh qwen3-32b-awq --with-reranker

# Reranker만 시작
./start.sh --reranker-only

# 테스트
curl http://localhost:8000/v1/models     # LLM
curl http://localhost:8001/health        # Reranker

# 종료
./stop.sh                # 전체 종료
./stop.sh llm            # LLM만 종료 (reranker 유지)
./stop.sh reranker       # Reranker만 종료
```

## 서비스 관리

### LLM 모델 교체 (Reranker 무중단)

```bash
./stop.sh llm                        # LLM만 중지
./start.sh qwen3.5-35b               # 새 모델로 시작
# → Reranker는 계속 실행중
```

### 서비스별 로그

```bash
docker compose logs -f vllm          # LLM 로그
docker compose logs -f reranker      # Reranker 로그
./stop.sh logs vllm                  # 단축 명령
```

### 상태 확인

```bash
./stop.sh status                     # 전체 상태
./health_check.sh                    # 헬스 체크
./health_check.sh -w                 # 지속 모니터링
./health_check.sh -j                 # JSON 출력
```

## 지원 모델

### LLM

| Config | 모델 | 유형 | VRAM | 비고 |
|--------|------|------|------|------|
| `qwen3-32b-awq` | Qwen3-32B-AWQ | Dense AWQ | ~18GB | 기존 운영 |
| `qwen3.5-35b` | Qwen3.5-35B-A3B-GPTQ-Int4 | MoE GPTQ | ~20GB | 최신, 128K ctx |
| `qwen3.5-27b` | Qwen3.5-27B | Dense BF16 | ~54GB | 코딩/추론 |
| `nemotron-nano` | Nemotron-3-Nano-30B | MoE BF16 | ~60GB | reasoning 토글 |
| `qwen3-30b-thinking` | Qwen3-30B-A3B-Thinking | MoE BF16 | ~60GB | always-on reasoning |

### Reranker

| 모델 | 크기 | VRAM | 비고 |
|------|------|------|------|
| **BAAI/bge-reranker-v2-m3** (기본) | 568M | ~1.1GB | Apache 2.0, 100+ 언어 |

## API 사용

### LLM — Chat Completions (포트 8000)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-32B-AWQ",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 4096
  }'
```

### Reranker — Score (포트 8001)

```bash
curl -X POST http://localhost:8001/v1/score \
  -H "Content-Type: application/json" \
  -d '{
    "model": "BAAI/bge-reranker-v2-m3",
    "text_1": "What is deep learning?",
    "text_2": [
      "Deep learning is a subset of machine learning",
      "The weather is nice today",
      "Neural networks have multiple layers"
    ]
  }'
```

### Python 클라이언트

```python
from openai import OpenAI

# LLM
llm = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")
response = llm.chat.completions.create(
    model="Qwen/Qwen3-32B-AWQ",
    messages=[{"role": "user", "content": "Hello!"}],
)

# Reranker (httpx 직접 호출)
import httpx
scores = httpx.post("http://localhost:8001/v1/score", json={
    "model": "BAAI/bge-reranker-v2-m3",
    "text_1": "query",
    "text_2": ["doc1", "doc2", "doc3"]
}).json()
```

## 설정 파일 구조

```yaml
model:
  name: "qwen3-32b-awq"
  path: "Qwen/Qwen3-32B-AWQ"
  description: "설명"

vllm:
  port: 8000
  tensor_parallel_size: 2
  max_model_len: 32768
  gpu_memory_utilization: 0.80
  dtype: "auto"
  reasoning_parser: "deepseek_r1"
  enable_auto_tool_choice: true
  tool_call_parser: "hermes"
  trust_remote_code: true
  enable_prefix_caching: true
  env: {}
  extra_args: []
```

## 새 모델 추가

1. `configs/`에 YAML 파일 생성 (기존 파일 복사 후 수정)
2. `model.path` = HuggingFace 모델 경로
3. `vllm.*` = 서빙 파라미터 (tp, context length, memory 등)
4. `./start.sh <새_모델_이름>`

## 문제 해결

### OOM

```yaml
vllm:
  max_model_len: 16384
  gpu_memory_utilization: 0.70
  enforce_eager: true
```

### Reranker + LLM 동시 실행 시 GPU 메모리 부족

`.env`에서 `RERANKER_GPU_UTIL`을 낮추거나 (기본 0.05), LLM config의 `gpu_memory_utilization`을 줄이세요.

### 신규 모델 아키텍처 미지원

```bash
# nightly 이미지 사용
./start.sh qwen3.5-35b --tag nightly
```

### 로그 확인

```bash
docker compose logs -f vllm
docker compose logs -f reranker
docker compose logs --tail 100
```
