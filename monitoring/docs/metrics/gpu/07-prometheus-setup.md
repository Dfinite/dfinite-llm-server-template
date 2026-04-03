# 7. Prometheus 구축 (Docker, Alloy 통합 기준)

문서 **5번**(Alloy)·**6번**(dcgm-exporter 타깃)을 거친 뒤, **Prometheus**는 Alloy가 넘긴 시계열을 **저장·PromQL 조회**하는 역할로 기동합니다.

Alloy 통합 수집 구조에서 **Prometheus**는 메트릭을 직접 scrape하지 않고,  
Alloy가 전달한 시계열을 **저장·조회**하는 역할로 기동합니다.

---

## 목표

- [x] Prometheus 이미지 선정
- [x] `prometheus.yml` 작성 (self scrape 최소 설정)
- [x] Docker 실행 방식 정의
- [x] remote_write 수신 활성화
- [x] Prometheus 컨테이너 정상 실행

---

## 7.1 이미지

| 항목 | 값 |
|------|-----|
| 이미지 | `prom/prometheus:v2.52.0` |
| UI | `http://localhost:9090` |

---

## 7.2 설정 파일

- 경로: [`prometheus/prometheus.yml`](../../../prometheus/prometheus.yml)
- `scrape_configs`:
  - **prometheus**: 자기 자신(`localhost:9090`)만 유지
- 런타임 플래그:
  - `--web.enable-remote-write-receiver` 활성화 (`docker-compose.yml`)

> `dcgm-exporter`, `vllm` 수집은 Prometheus가 아니라 Alloy(`alloy/config.alloy`)에서 수행합니다.

---

## 7.3 실행

Alloy 통합 구조에서는 **Alloy가 메트릭을 수집**하고 **Prometheus가 저장/조회**를 담당하므로,  
실제 메트릭 파이프라인 검증 시에는 두 컨테이너를 함께 실행합니다.

```bash
docker compose up -d prometheus alloy
```

GPU 스택까지 포함:

```bash
docker compose --profile gpu up -d
```

> Prometheus만 단독 실행은 가능하지만, 이 경우 dcgm-exporter/vLLM 메트릭은 수집되지 않습니다. (Alloy가 scrape 주체)

확인:

```bash
docker compose ps
curl -sS http://127.0.0.1:9090/-/healthy
curl -sS http://127.0.0.1:9090/api/v1/status/runtimeinfo
```

브라우저: **Graph** (`http://localhost:9090/graph`)

---

## 7.4 완료 조건

| 항목 | 값 |
|------|-----|
| 설정 파일 | `prometheus/prometheus.yml` |
| 실행 명령 | `docker compose up -d prometheus alloy` |
| 컨테이너 상태 | UP — [UI 캡처](../../../src/03-prometheus-graph-ui.png) |
| 접속 URL | `http://<호스트>:9090` |
| 역할 | Alloy remote_write 수신, TSDB 저장, PromQL 조회 |

---

## 참고

- [Prometheus Docker 문서](https://prometheus.io/docs/prometheus/latest/installation/#using-docker)
- Alloy 통합 구조: [`docs/overview/01-alloy-unified-collection-architecture.md`](../../overview/01-alloy-unified-collection-architecture.md)
- GPU 스택과 함께: `docker compose --profile gpu up -d` (문서 [03](./03-dcgm-and-dcgm-exporter-setup.md))
- Alloy·dcgm 타깃: 문서 [5번](./05-alloy-setup.md), [6번](./06-alloy-dcgm-exporter.md)
- Grafana: 문서 [10번](./10-grafana-setup.md)
- Grafana Prometheus 데이터 소스·GPU 대시보드: [11번](./11-grafana-prometheus-datasource.md), [12번](./12-gpu-grafana-dashboard.md)
