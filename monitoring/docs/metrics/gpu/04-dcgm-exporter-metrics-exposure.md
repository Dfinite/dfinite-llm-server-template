# 4. dcgm-exporter 메트릭 노출 확인

dcgm-exporter가 **Prometheus exposition 형식**의 메트릭을 HTTP로 정상 노출하는지 확인합니다.  
**수집(scrape) 주체는 Prometheus가 아니라 Alloy**이며, Alloy가 긁은 시계열은 Prometheus에 적재됩니다. 본 문서는 **엔드포인트·본문**만 검증합니다 — scrape 설정은 [5번 — Alloy](./05-alloy-setup.md)·[6번 — dcgm 타깃](./06-alloy-dcgm-exporter.md), `alloy/config.alloy` 를 참고합니다.

| 구분 | 담당 |
|------|------|
| **노출** | dcgm-exporter — `:9400/metrics` (이 문서에서 `curl` 등으로 확인) |
| **수집** | **Alloy** — `prometheus.scrape` 로 동일 URL 대상 scrape |
| **저장·조회** | **Prometheus** — `remote_write` 수신 후 PromQL |

## 목표

- [x] `/metrics` endpoint 호출 및 응답 확인
- [x] 노출 메트릭 목록 확인
- [x] 주요 GPU 메트릭 존재 여부 확인
- [x] GPU별 label 구조 확인

---

## 4.1 `/metrics` endpoint 호출

### 확인 명령

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9400/metrics
curl -sS http://127.0.0.1:9400/metrics | head -n 50
```

### 결과 요약

| 항목 | 기대 |
|------|------|
| HTTP 상태 | `200` |
| 본문 | `# HELP` / `# TYPE` 및 `DCGM_` 시리즈 포함 |

---

## 4.2 노출 메트릭 목록 확인

### 확인 명령

```bash
curl -sS http://127.0.0.1:9400/metrics | grep -E '^DCGM_FI_' | sed 's/{.*//' | sort -u
```

`# TYPE` 줄만 보려면:

```bash
curl -sS http://127.0.0.1:9400/metrics | grep '^# TYPE DCGM'
```

### 결과

전체 정의는 NVIDIA [default-counters.csv](https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv) 와 비교할 수 있습니다. 실제 노출은 버전·프로파일에 따라 부분집합일 수 있습니다.

---

## 4.3 주요 GPU 메트릭 존재 여부 확인

| 목적 | 메트릭명 | 단위 |
|------|----------|------|
| GPU 사용률 | `DCGM_FI_DEV_GPU_UTIL` | % |
| GPU 온도 | `DCGM_FI_DEV_GPU_TEMP` | °C |
| VRAM 사용량 | `DCGM_FI_DEV_FB_USED` | MiB |
| 전력 | `DCGM_FI_DEV_POWER_USAGE` | W |

### 확인 명령

```bash
curl -sS http://127.0.0.1:9400/metrics | grep -E '^DCGM_FI_DEV_(GPU_UTIL|GPU_TEMP|FB_USED|POWER_USAGE)\{'
```

### 결과 요약

위 네 이름이 각각 최소 1시리즈 이상이면 [2번 §2.6](./02-gpu-metrics-sources.md) 에 적어 둔 용도를 충족합니다.

---

## 4.4 GPU별 label 확인

`/metrics` 한 줄의 `{…}` 안에서 라벨 키를 확인합니다. 멀티 GPU면 동일 메트릭명이 `gpu="0"`, `gpu="1"` … 으로 반복됩니다.

### 결과

| 라벨 | 의미 |
|------|------|
| `gpu` | 인덱스 `"0"`, `"1"` … |
| `UUID` | GPU UUID |
| `device` | 예: `nvidia0` |
| `modelName`, `pci_bus_id`, `Hostname`, `DCGM_FI_DRIVER_VERSION` | 환경·템플릿에 따라 |

---

## 4.5 응답 발췌 예시

```text
# TYPE DCGM_FI_DEV_GPU_TEMP gauge
DCGM_FI_DEV_GPU_TEMP{gpu="0",UUID="GPU-…",device="nvidia0",modelName="NVIDIA L40S",…} 59
DCGM_FI_DEV_GPU_TEMP{gpu="1",UUID="GPU-…",device="nvidia1",modelName="NVIDIA L40S",…} 51
# TYPE DCGM_FI_DEV_POWER_USAGE gauge
DCGM_FI_DEV_POWER_USAGE{gpu="0",…} 122.855
DCGM_FI_DEV_POWER_USAGE{gpu="1",…} 109.961
# TYPE DCGM_FI_DEV_FB_USED gauge
DCGM_FI_DEV_FB_USED{gpu="0",…} 39392
DCGM_FI_DEV_FB_USED{gpu="1",…} 39392
```

> 유휴 시 `DCGM_FI_DEV_GPU_UTIL` 이 0 일 수 있습니다. `DCGM_FI_DEV_MEMORY_TEMP` 가 0 인 경우도 하드웨어·필드에 따라 있습니다.

---

## 4.6 사용 예정 메트릭명 메모

```text
DCGM_FI_DEV_GPU_UTIL
DCGM_FI_DEV_GPU_TEMP
DCGM_FI_DEV_FB_USED
DCGM_FI_DEV_POWER_USAGE
```

> 커스텀 counter CSV를 쓰면 이름이 달라질 수 있으므로, 실제 배포의 `/metrics`를 최종 기준으로 합니다.

---

## 완료 조건

- [x] `/metrics` 호출 성공, 응답 예시 기록
- [x] 주요 메트릭명 목록 정리
- [x] 라벨 구조 정리
- [x] 사용 예정 메트릭명 메모

---

## 메모 / 이슈

| 항목 | 내용 |
|------|------|
| 메트릭명 변경 | exporter·DCGM 버전 업 시 `default-counters.csv`와 재대조. |

---

## 참고

- [dcgm-exporter (GitHub)](https://github.com/NVIDIA/dcgm-exporter)
- [default-counters.csv](https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv)
