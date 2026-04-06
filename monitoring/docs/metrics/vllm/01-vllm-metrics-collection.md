# 1. vLLM 메트릭 수집 환경 확인 (Alloy 통합)

vLLM 서버가 노출하는 `/metrics` 엔드포인트를 Alloy가 수집하고 Prometheus에 저장하여, LLM 서비스 지표를 모니터링합니다.

---

## 목표

- [x] vLLM 컨테이너 `/metrics` 엔드포인트 확인
- [x] Alloy `vllm` 타깃 추가 및 메트릭 저장 확인
- [x] 수집 메트릭 분류 및 대시보드 활용 메트릭 선정

---

## 1.1 vLLM 컨테이너 정보

`manage_compose.py add`로 등록된 서비스는 `vllm-{서비스명}` 형태의 컨테이너명으로 생성됩니다.

| 항목 | 형식 | 예시 |
|------|------|------|
| 컨테이너명 | `vllm-{name}` | `vllm-my-llm` |
| service 라벨 | `monitoring.service={name}` | `monitoring.service=my-llm` |
| 포트 | `services.json`에 등록된 포트 | `10071` |
| `/metrics` 엔드포인트 | `http://vllm-{name}:{port}/metrics` | `http://vllm-my-llm:10071/metrics` |

등록된 서비스 목록 확인: `./scripts/manage_compose.py list`

---

## 1.2 Alloy 스크래핑 설정

`alloy/config.alloy`는 Docker 레이블 기반 자동 발견을 사용합니다. `manage_compose.py add`로 서비스를 등록하면 컨테이너에 아래 레이블이 자동으로 붙으며, 별도 설정 없이 Alloy가 감지합니다.

```yaml
labels:
  monitoring.scrape: "true"
  monitoring.port: "10071"
  monitoring.job: "vllm"
  monitoring.service: "my-llm"
```

Alloy의 `discovery.docker` 블록이 이 레이블을 감지하여 `vllm-my-llm:10071/metrics`를 scrape 대상으로 추가합니다. 서비스 추가/삭제 시 `alloy/config.alloy` 수정이 불필요합니다.

`job="vllm"`으로 통일하고 `service` 라벨로 인스턴스를 구분합니다. `model_name` 라벨은 vLLM이 자동으로 붙여주지만 전체 모델 경로라 필터로 쓰기 불편하므로, 짧은 alias로 `service`를 활용합니다.

### 타겟 확인

| 항목 | 값 |
|------|-----|
| 타겟 발견 방식 | Docker 레이블 (`monitoring.scrape=true`) |
| 타겟 주소 형식 | `vllm-{name}:{port}` (llm-net 네트워크 내 컨테이너명) |
| 수집 주체 | Alloy |
| 저장소 | Prometheus (remote_write 수신) |
| 확인 방법 | Prometheus Graph에서 `{job="vllm"}` 조회 |

---

## 1.3 수집 메트릭 분류

vLLM이 노출하는 391개 샘플 중 대부분은 histogram bucket의 반복입니다. 실질적으로 의미 있는 메트릭을 카테고리별로 분류합니다.

### 토큰 처리량

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `vllm:prompt_tokens_total` | counter | 누적 입력 토큰 수 |
| `vllm:generation_tokens_total` | counter | 누적 생성 토큰 수 |

### 요청 상태

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `vllm:num_requests_running` | gauge | 현재 추론 중인 요청 수 |
| `vllm:num_requests_waiting` | gauge | 대기열에 쌓인 요청 수 |
| `vllm:request_success_total` | counter | 완료된 요청 수 (`finished_reason` 라벨: stop, length, abort) |

### 레이턴시 (histogram)

| 메트릭 | 설명 |
|--------|------|
| `vllm:time_to_first_token_seconds` | 첫 토큰 생성까지 걸린 시간 (TTFT) |
| `vllm:time_per_output_token_seconds` | 토큰 1개 생성 시간 |
| `vllm:e2e_request_latency_seconds` | 요청 전체 응답 시간 |
| `vllm:request_queue_time_seconds` | 대기열 대기 시간 |
| `vllm:request_prefill_time_seconds` | Prefill 단계 소요 시간 |
| `vllm:request_decode_time_seconds` | Decode 단계 소요 시간 |

### KV 캐시 · GPU 메모리

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `vllm:gpu_cache_usage_perc` | gauge | KV 캐시 점유율 (0.0–1.0) |
| `vllm:num_preemptions_total` | counter | 선점(preemption) 발생 수 |
| `vllm:gpu_prefix_cache_hits_total` | counter | 프리픽스 캐시 히트 수 |
| `vllm:gpu_prefix_cache_queries_total` | counter | 프리픽스 캐시 조회 수 |

### HTTP 엔드포인트

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `http_requests_total` | counter | 핸들러·상태코드별 HTTP 요청 수 |
| `http_request_duration_seconds` | histogram | HTTP 응답 시간 |

### 프로세스 · 런타임

| 메트릭 | 설명 |
|--------|------|
| `process_resident_memory_bytes` | RSS 메모리 |
| `process_cpu_seconds_total` | 누적 CPU 시간 |
| `python_info` | Python 런타임 정보 |

---

## 1.4 대시보드 활용 메트릭 선정

수집된 메트릭 중 대시보드에 표출할 항목을 선정합니다. GPU 메트릭(dcgm-exporter)은 인프라 관점, vLLM 메트릭은 서비스 관점의 보조 지표로 활용합니다.

### 내부 운영 모니터링

GPU 하드웨어 상태와 LLM 서비스 성능을 교차 분석하여 문제 원인을 파악합니다.

| 패널 | PromQL | 용도 |
|------|--------|------|
| 토큰 처리 속도 | `rate(vllm:prompt_tokens_total[5m])`, `rate(vllm:generation_tokens_total[5m])` | 입력/생성 토큰 초당 처리량 |
| 현재 요청 수 | `vllm:num_requests_running`, `vllm:num_requests_waiting` | 실시간 부하 |
| TTFT p95 | `histogram_quantile(0.95, rate(vllm:time_to_first_token_seconds_bucket[5m]))` | 첫 토큰 응답 성능 |
| E2E Latency p95 | `histogram_quantile(0.95, rate(vllm:e2e_request_latency_seconds_bucket[5m]))` | 전체 응답 성능 |
| KV 캐시 사용률 | `vllm:gpu_cache_usage_perc` | VRAM 캐시 압박도 |

### 고객사 공유용

서비스 수준 지표를 표출합니다.

| 패널 | PromQL |
|------|--------|
| 토큰 사용량 누적 | `vllm:prompt_tokens_total`, `vllm:generation_tokens_total` |
| 토큰 처리 속도 | `rate(vllm:generation_tokens_total[5m])` |
| 요청 수 | `vllm:request_success_total` |
| 평균 응답 시간 | `rate(vllm:e2e_request_latency_seconds_sum[5m]) / rate(vllm:e2e_request_latency_seconds_count[5m])` |
| GPT-4o 환산 비용 | `(vllm:prompt_tokens_total * 2.5 / 1e6) + (vllm:generation_tokens_total * 10 / 1e6)` |
| Gemini 2.5 Pro 환산 비용 | `(vllm:prompt_tokens_total * 1.25 / 1e6) + (vllm:generation_tokens_total * 10 / 1e6)` |
| GPT-4o-mini 환산 비용 | `(vllm:prompt_tokens_total * 0.15 / 1e6) + (vllm:generation_tokens_total * 0.6 / 1e6)` |
| Gemini 2.5 Flash 환산 비용 | `(vllm:prompt_tokens_total * 0.3 / 1e6) + (vllm:generation_tokens_total * 2.5 / 1e6)` |

> **참고:** API 환산 비용은 2026-03-25 기준 단가입니다. 단가 변동 시 PromQL 상수를 갱신해야 합니다.

---

## 완료 조건

- [x] vLLM `/metrics` 엔드포인트 접근 가능
- [x] Alloy `vllm` 타깃 수집 확인
- [x] 수집 메트릭 391개 확인 (scrape_samples_scraped)
- [x] 대시보드 활용 메트릭 선정 완료

---

## 메모 / 이슈

| 항목 | 내용 |
|------|------|
| Docker 네트워크 | Alloy와 vLLM이 `llm-net` 공유 네트워크에 있으므로 컨테이너명으로 직접 접근 가능. |
| 이전 타겟 잔여 | 과거 타깃 변경 시 `up=0` 잔여 시계열이 남을 수 있음. 수집 타깃 정리 후 시간 경과로 자동 소멸. |
| 환산 비용 단가 | GPT-4o $2.50/$10.00 · Gemini 2.5 Pro $1.25/$10.00 · GPT-4o-mini $0.15/$0.60 · Gemini 2.5 Flash $0.30/$2.50 (입력/출력, /1M 토큰, 2026-03-25 기준). |

---

## 참고

| 문서 | 내용 |
|------|------|
| [GPU-07 — Prometheus 구축](../gpu/07-prometheus-setup.md) | Prometheus 저장·조회 |
| [GPU-12 — GPU 대시보드](../gpu/12-gpu-grafana-dashboard.md) | GPU 대시보드 패널 구성 참고 |
| [개요-01 — Alloy 통합 수집](../../overview/01-alloy-unified-collection-architecture.md) | Alloy 통합 아키텍처 |
