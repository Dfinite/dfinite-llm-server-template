# 3. vLLM 메트릭 PromQL 레퍼런스

vLLM `/metrics` 엔드포인트가 노출하는 메트릭을 대상으로, Prometheus UI 또는 Grafana Explore에서 사용할 **PromQL**을 정리합니다.

---

## 목표

- [x] 주요 vLLM 메트릭명 및 PromQL 정리
- [x] 라벨 필터링 방법 정리
- [x] Prometheus / Grafana Explore에서 동작 확인

> 메트릭명은 [01](./01-vllm-metrics-collection.md)에서 실측 확인한 이름 기준. vLLM 버전에 따라 이름이 달라질 수 있으므로 `/metrics`에서 재확인.

---

## 3.1 라벨

vLLM 메트릭에 공통으로 붙는 라벨입니다.

| 라벨 | 의미 | 예시 |
|------|------|------|
| `model_name` | 로드된 모델 경로 | `Qwen/Qwen2.5-VL-32B-Instruct-AWQ` |
| `finished_reason` | 요청 종료 사유 (request_success) | `stop`, `length`, `abort` |
| `le` | histogram bucket 상한 | `0.5`, `1.0`, `+Inf` |

**특정 모델만 보기**

```promql
vllm:prompt_tokens_total{model_name="Qwen/Qwen2.5-VL-32B-Instruct-AWQ"}
```

**모든 모델 (regex)**

```promql
vllm:prompt_tokens_total{model_name=~".+"}
```

---

## 3.2 토큰

### 누적 토큰 수

```promql
vllm:prompt_tokens_total
vllm:generation_tokens_total
```

### 토큰 처리 속도 (tok/s)

```promql
rate(vllm:prompt_tokens_total[5m])
rate(vllm:generation_tokens_total[5m])
```

---

## 3.3 요청

### 현재 요청 수 (실시간)

```promql
vllm:num_requests_running
vllm:num_requests_waiting
```

### 완료 요청 수 (누적)

```promql
vllm:request_success_total{finished_reason="stop"}
vllm:request_success_total{finished_reason="length"}
vllm:request_success_total{finished_reason="abort"}
```

### 요청 처리율 (req/s)

```promql
rate(vllm:request_success_total[5m])
```

---

## 3.4 레이턴시

### 평균 응답 시간

```promql
rate(vllm:e2e_request_latency_seconds_sum[5m])
  / rate(vllm:e2e_request_latency_seconds_count[5m])
```

### E2E Latency 백분위

```promql
histogram_quantile(0.5, rate(vllm:e2e_request_latency_seconds_bucket[5m]))
histogram_quantile(0.95, rate(vllm:e2e_request_latency_seconds_bucket[5m]))
histogram_quantile(0.99, rate(vllm:e2e_request_latency_seconds_bucket[5m]))
```

### Time to First Token (TTFT)

```promql
histogram_quantile(0.5, rate(vllm:time_to_first_token_seconds_bucket[5m]))
histogram_quantile(0.95, rate(vllm:time_to_first_token_seconds_bucket[5m]))
```

### 토큰 1개 생성 시간

```promql
histogram_quantile(0.5, rate(vllm:time_per_output_token_seconds_bucket[5m]))
histogram_quantile(0.95, rate(vllm:time_per_output_token_seconds_bucket[5m]))
```

### Prefill / Decode 시간

```promql
histogram_quantile(0.95, rate(vllm:request_prefill_time_seconds_bucket[5m]))
histogram_quantile(0.95, rate(vllm:request_decode_time_seconds_bucket[5m]))
```

### 대기열 대기 시간

```promql
histogram_quantile(0.95, rate(vllm:request_queue_time_seconds_bucket[5m]))
```

---

## 3.5 KV 캐시 · 메모리

### KV 캐시 사용률

```promql
vllm:gpu_cache_usage_perc
```

> 0.0–1.0 범위. Grafana에서 `percentunit`으로 표시하면 `%`로 변환됩니다.

### 선점 횟수 (누적)

```promql
vllm:num_preemptions_total
```

### 프리픽스 캐시 히트율

```promql
vllm:gpu_prefix_cache_hits_total / vllm:gpu_prefix_cache_queries_total
```

---

## 3.6 HTTP 엔드포인트

### 핸들러별 요청 수

```promql
rate(http_requests_total{job="vllm"}[5m])
```

### HTTP 응답 시간 p95

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="vllm"}[5m]))
```

---

## 3.7 동작 확인

테스트 요청을 보낸 뒤 Prometheus API로 주요 쿼리의 반환값을 검증합니다.

### 테스트 요청

```bash
curl -s http://localhost:30071/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-VL-32B-Instruct-AWQ",
       "messages": [{"role": "user", "content": "Hi"}],
       "max_tokens": 10}'
```

응답: prompt 20토큰, completion 10토큰, `finish_reason: "length"`.

### 검증 결과

| 카테고리 | 쿼리 | 결과 | 판정 |
|----------|------|------|------|
| 토큰 | `vllm:prompt_tokens_total` | 4,474,787 | ✅ |
| KV 캐시 | `vllm:gpu_cache_usage_perc` | 0.00008 (≈0.008%) | ✅ |
| 요청 | `vllm:num_requests_running` | 0 (유휴 상태) | ✅ |
| 레이턴시 | `histogram_quantile(0.95, rate(vllm:e2e_request_latency_seconds_bucket[5m]))` | 0.29s | ✅ |

> 레이턴시 계열 쿼리(histogram_quantile, rate sum/count)는 최근 5분 이내 요청이 없으면 `NaN`을 반환합니다.

---

## 참고

- [문서 01 (vLLM 메트릭 수집 환경 확인)](./01-vllm-metrics-collection.md)
- [문서 GPU-08 (GPU 메트릭 PromQL)](../gpu/08-gpu-metrics-promql.md)
