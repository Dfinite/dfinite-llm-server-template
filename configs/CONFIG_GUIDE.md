# Config 작성 가이드

`configs/*.yaml` 파일은 `parse_config.py`를 통해 vLLM serve 명령어로 변환됩니다.

## 기본 구조

```yaml
model:
  name: "모델-이름"          # 컨테이너명에 사용 (vllm-{name})
  path: "Owner/Model-Name"  # HuggingFace 모델 경로
  description: "설명"        # --list에서 표시

vllm:
  port: 10071               # 호스트 포트
  tensor_parallel_size: 2   # GPU 분할 수
  max_model_len: 32768      # 최대 context 길이
  gpu_memory_utilization: 0.85
  dtype: "auto"

  # ... 추가 파라미터

  env: {}                   # 컨테이너 환경변수
  extra_args: []            # 추가 CLI 인자
```

## model 섹션

| 필드 | 필수 | 설명 | 예시 |
|------|------|------|------|
| `name` | O | 모델 식별자, 컨테이너명(`vllm-{name}`)에 사용 | `"qwen3-32b-awq"` |
| `path` | O | HuggingFace 모델 경로 | `"Qwen/Qwen3-32B-AWQ"` |
| `description` | - | `--list`에서 표시되는 설명 | `"Qwen3 32B AWQ — 경량 추론"` |

## vllm 섹션 - 핵심 파라미터

| 필드 | CLI 플래그 | 기본값 | 설명 |
|------|-----------|--------|------|
| `port` | `--port` | `10071` | vLLM 서버 포트 (호스트 포트로도 사용) |
| `tensor_parallel_size` | `--tensor-parallel-size` | - | GPU 분할 수. GPU 2장이면 `2` |
| `max_model_len` | `--max-model-len` | 모델 기본값 | 최대 context 길이 (토큰). VRAM에 따라 조절 |
| `gpu_memory_utilization` | `--gpu-memory-utilization` | - | GPU 메모리 사용 비율 (0.0~1.0). 높을수록 context 여유 |
| `dtype` | `--dtype` | - | 데이터 타입. `"auto"`, `"bfloat16"`, `"float16"` |
| `quantization` | `--quantization` | - | 양자화 방식. `"awq"`, `"gptq"`, `"moe_wna16"` 등 |

## vllm 섹션 - Reasoning / Tool calling

| 필드 | CLI 플래그 | 설명 |
|------|-----------|------|
| `reasoning_parser` | `--reasoning-parser` | thinking 모드 파서. `"qwen3"`, `"deepseek_r1"`, `"nano_v3"` 등 |
| `enable_auto_tool_choice` | `--enable-auto-tool-choice` | `true` 설정 시 자동 tool 호출 활성화 |
| `tool_call_parser` | `--tool-call-parser` | tool 호출 파서. `"qwen3_coder"`, `"hermes"` 등 |

## vllm 섹션 - Performance (bool 플래그)

`true`일 때만 CLI에 추가됩니다. `false`이면 무시.

| 필드 | CLI 플래그 | 설명 |
|------|-----------|------|
| `trust_remote_code` | `--trust-remote-code` | HuggingFace 커스텀 코드 실행 허용. 대부분 `true` 필요 |
| `enforce_eager` | `--enforce-eager` | CUDA graph 비활성화. 호환성 문제 시 `true` |
| `enable_prefix_caching` | `--enable-prefix-caching` | 프롬프트 프리픽스 캐싱. 반복 프롬프트 시 성능 향상 |

## vllm 섹션 - 기타

| 필드 | CLI 플래그 | 설명 |
|------|-----------|------|
| `logits_processor_pattern` | `--logits-processor-pattern` | logits processor 패턴 |
| `runner` | - | Embedding/Reranker용. `"pooling"` (LLM config에서는 사용 안 함) |

## env 섹션

컨테이너에 전달할 환경변수. key-value 형태.

```yaml
env:
  VLLM_ALLOW_LONG_MAX_MODEL_LEN: "1"    # max_model_len 제한 해제
  OMP_NUM_THREADS: "1"                   # 멀티모달 전처리 스레드 제한
```

## extra_args 섹션

parse_config.py가 직접 지원하지 않는 vLLM CLI 인자를 추가할 때 사용.
각 항목은 별도의 리스트 아이템으로 작성.

```yaml
extra_args:
  - "--language-model-only"                              # 비전 인코더 비활성화
  - "--default-chat-template-kwargs.enable_thinking"     # thinking 모드 비활성화
  - "false"
  - "--limit-mm-per-prompt.image"                        # 이미지 최대 3장
  - "3"
  - "--limit-mm-per-prompt.video"                        # 비디오 비활성화
  - "0"
  - "--max-num-batched-tokens"                           # 배치 토큰 제한
  - "2096"
```

> v0.18.0부터 JSON 값은 dot-notation을 사용합니다.
> `--limit-mm-per-prompt '{"image":3}'` 대신 `--limit-mm-per-prompt.image 3`

## LLM Config 예시

```yaml
model:
  name: "qwen3-32b-awq"
  path: "Qwen/Qwen3-32B-AWQ"
  description: "Qwen3 32B AWQ — 경량 추론"

vllm:
  port: 10071
  tensor_parallel_size: 2
  max_model_len: 32768
  gpu_memory_utilization: 0.85
  dtype: "auto"
  quantization: "awq"

  reasoning_parser: "qwen3"
  enable_auto_tool_choice: true
  tool_call_parser: "qwen3_coder"

  trust_remote_code: true
  enforce_eager: false
  enable_prefix_caching: true

  env: {}
  extra_args:
    - "--default-chat-template-kwargs.enable_thinking"
    - "false"
```

## Embedding Config 예시

Embedding config는 `embedding-` 접두사를 사용합니다.
docker-compose의 `EMBEDDING_*` 환경변수로 반영됩니다.

```yaml
model:
  name: "bge-m3"
  path: "BAAI/bge-m3"
  description: "BGE-M3 568M — 다국어 embedding, 1024dim"

vllm:
  port: 10073
  runner: "pooling"          # embedding/reranker는 pooling 필수
  tensor_parallel_size: 1
  max_model_len: 8192
  gpu_memory_utilization: 0.10
  dtype: "auto"
  trust_remote_code: true
```

## VRAM 산정 가이드

| dtype | 계산 | 예시 (27B) |
|-------|------|------------|
| BF16/FP16 | params x 2 bytes | 27B x 2 = ~54GB |
| INT8 | params x 1 byte | 27B x 1 = ~27GB |
| INT4 (AWQ/GPTQ) | params x 0.5 bytes | 27B x 0.5 = ~13.5GB |

실제 VRAM = 모델 가중치 + KV cache + 오버헤드.
`gpu_memory_utilization`으로 KV cache에 할당할 VRAM 비율을 조절합니다.

| GPU | VRAM | gpu_util=0.85 | gpu_util=0.90 |
|-----|------|---------------|---------------|
| A6000 | 48GB | 40.8GB 사용 가능 | 43.2GB 사용 가능 |
| L40S | 45GB | 38.3GB 사용 가능 | 40.5GB 사용 가능 |

## 파일 명명 규칙

| 유형 | 패턴 | 예시 |
|------|------|------|
| LLM | `{모델명}.yaml` | `qwen3-32b-awq.yaml` |
| Embedding | `embedding-{모델명}.yaml` | `embedding-bge-m3.yaml` |
| Reranker | `reranker.yaml` | (docker-compose에 내장) |
