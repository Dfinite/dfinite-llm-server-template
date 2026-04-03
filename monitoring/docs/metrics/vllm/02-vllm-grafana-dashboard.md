# 2. vLLM 대시보드 패널 구성

vLLM 서비스 메트릭을 Grafana 패널로 구성합니다. [01](./01-vllm-metrics-collection.md)에서 Prometheus 수집이 확인된 상태에서 진행합니다.

---

## 목표

- [x] 토큰 사용량 누적 패널 구성
- [x] 토큰 처리 속도 패널 구성
- [x] 요청 수 패널 구성
- [x] 평균 응답 시간 패널 구성
- [x] API 환산 비용 패널 구성 (플래그십 / 경량)
- [x] Grafana에서 대시보드 표시 확인

---

## 2.1 대시보드 로드

GPU 대시보드와 동일하게 provisioning으로 자동 로드됩니다.

| 항목 | 값 |
|------|-----|
| Provider | [`grafana/provisioning/dashboards/default.yaml`](../../../grafana/provisioning/dashboards/default.yaml) |
| 대시보드 JSON | [`grafana/dashboards/vllm-overview.json`](../../../grafana/dashboards/vllm-overview.json) |
| 대시보드 이름 | vLLM Overview |
| UID | `vllm-overview` |

Grafana UI: **Dashboards → vLLM Overview** 선택.

---

## 2.2 패널 구성

### 토큰 사용량 (누적)

| 항목 | 값 |
|------|-----|
| PromQL | `vllm:prompt_tokens_total` (입력), `vllm:generation_tokens_total` (생성) |
| 단위 | none |
| 타입 | timeseries |

### 토큰 처리 속도

| 항목 | 값 |
|------|-----|
| PromQL | `rate(vllm:prompt_tokens_total[5m])` (입력), `rate(vllm:generation_tokens_total[5m])` (생성) |
| 단위 | none (tok/s) |
| 타입 | timeseries |

### 요청 수

| 항목 | 값 |
|------|-----|
| PromQL | `vllm:request_success_total` (`finished_reason` 라벨: stop, length, abort) |
| 단위 | none |
| 타입 | timeseries |

### 평균 응답 시간

| 항목 | 값 |
|------|-----|
| PromQL | `rate(vllm:e2e_request_latency_seconds_sum[5m]) / rate(vllm:e2e_request_latency_seconds_count[5m])` |
| 단위 | s |
| 타입 | timeseries |

### API 환산 비용

플래그십과 경량을 각각 한 패널에 GPT / Gemini를 함께 표시합니다.

| 패널 | 시리즈 | PromQL |
|------|--------|--------|
| 플래그십 | GPT-4o | `(prompt * 2.5 / 1e6) + (generation * 10 / 1e6)` |
| | Gemini 2.5 Pro | `(prompt * 1.25 / 1e6) + (generation * 10 / 1e6)` |
| 경량 | GPT-4o-mini | `(prompt * 0.15 / 1e6) + (generation * 0.6 / 1e6)` |
| | Gemini 2.5 Flash | `(prompt * 0.3 / 1e6) + (generation * 2.5 / 1e6)` |

| 모델 | 입력 (/1M) | 출력 (/1M) | 출처 |
|------|-----------|-----------|------|
| GPT-4o | $2.50 | $10.00 | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing) |
| Gemini 2.5 Pro | $1.25 | $10.00 | [Gemini Pricing](https://ai.google.dev/gemini-api/docs/pricing?hl=ko) |
| GPT-4o-mini | $0.15 | $0.60 | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing) |
| Gemini 2.5 Flash | $0.30 | $2.50 | [Gemini Pricing](https://ai.google.dev/gemini-api/docs/pricing?hl=ko) |

> 2026-03-25 기준 단가. 토크나이저 차이 등으로 실제 API 비용과 차이가 있을 수 있습니다.

---

## 2.3 JSON 수정 후 재생성

```bash
make grafana-vllm-dashboard
# 또는
python3 scripts/build_grafana_vllm_dashboard.py
```

변경 반영 시 `docker compose restart grafana`로 provisioning을 재로드합니다.

---

## 2.4 완료 조건

| 완료 조건 | 작성할 내용 | 상태 |
|-----------|-------------|------|
| 대시보드 패널 표시 확인 | Grafana 대시보드 캡처 | ✅ 아래 참조 |

![vLLM Dashboard](../../../src/vllm-dashboard-overview.png)
| 토큰·요청·응답시간 그래프 정상 | 패널별 PromQL 정리 | ✅ [2.2 참조](#22-패널-구성) |
| API 환산 비용 표시 확인 | 단가 기준일 명시 | ✅ 2026-03-25 |

---

## 참고

- 문서 [01 (vLLM 메트릭 수집 환경 확인)](./01-vllm-metrics-collection.md)
- 문서 [GPU-12 (GPU 대시보드 패널 구성)](../gpu/12-gpu-grafana-dashboard.md)
