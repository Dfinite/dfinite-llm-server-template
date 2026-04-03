# 5. Alloy 구축 (메트릭 파트)

**Grafana Alloy**가 HTTP `/metrics`를 **scrape**하고, 수집한 시계열을 **Prometheus** `remote_write`로 넘기는 **메트릭 파이프라인**만 정리합니다.

> **로그 수집**(Loki·Docker 로그·소켓 마운트 등)은 [`docs/logs/`](../../logs/01-loki-setup.md)의 Loki·Alloy 문서를 따릅니다. 본 문서는 **`prometheus.scrape` · `prometheus.remote_write`** 에 해당하는 부분만 다룹니다.

> **문서 순서**: **5 Alloy → 6 Alloy·dcgm-exporter 연동 → 7 Prometheus(저장)**. 런타임에서는 `docker compose` 로 `alloy`·`prometheus`·GPU 스택을 **같이** 기동하는 경우가 많습니다.

---

## 목표

- [ ] Alloy 이미지·포트·[`alloy/config.alloy`](../../alloy/config.alloy) 경로 파악
- [ ] `prometheus.scrape` · `prometheus.remote_write` 블록이 메트릭 흐름에서 하는 일 이해
- [ ] (검증) [6번](./06-alloy-dcgm-exporter.md)·[7번](./07-prometheus-setup.md)까지 반영한 뒤 Prometheus UI에서 시계열이 보이는지 확인

---

## 5.1 이미지·포트

| 항목 | 값 |
|------|-----|
| 이미지 | `grafana/alloy:v1.3.1` |
| 명령 | `run /etc/alloy/config.alloy` |
| UI (기본) | `12345` — Compose에서 `12345:12345` 로 노출 |
| 설정 파일 (컨테이너) | `/etc/alloy/config.alloy` |

`depends_on` 등은 Compose 정의에 따릅니다. **메트릭 sink**는 `http://prometheus:9090/api/v1/write` 를 가리킵니다.

---

## 5.2 `config.alloy` — 메트릭 블록만

- 경로: [`alloy/config.alloy`](../../alloy/config.alloy)

| 블록 | 역할 |
|------|------|
| `prometheus.scrape` | `dcgm-exporter`, vLLM, Prometheus self 등 **정적 타깃** scrape |
| `prometheus.remote_write` | 수집분을 Prometheus **remote_write 수신 API**로 전달 |

타깃 예(요약):

- `dcgm-exporter:9400` (`job="dcgm-exporter"`) — GPU 프로필로 exporter가 떠 있을 때
- `172.17.0.1:30071` (`job="vllm"`, `service="qwen-demo"`) — 호스트 vLLM chat 인스턴스 ([vLLM-01](../vllm/01-vllm-metrics-collection.md))
- `172.17.0.1:30072` (`job="vllm"`, `service="embedding-women"`) — 호스트 vLLM embedding 인스턴스
- `prometheus:9090` (`job="prometheus"`) — Prometheus self

GPU별 scrape·검증 절차는 [6번 — Alloy — dcgm-exporter 연동](./06-alloy-dcgm-exporter.md)에서 다룹니다.

---

## 5.3 실행

`monitoring/` 디렉터리에서 **저장소(Prometheus)와 함께** 기동하는 예:

```bash
docker compose up -d prometheus alloy
```

Compose에 정의된 **전체 모니터링 스택** 기동:

```bash
docker compose --profile gpu up -d
```

> `remote_write` 대상인 Prometheus가 없으면 메트릭 적재는 되지 않습니다. 문서 순서는 **5 → 6 → 7**이며, 기동은 `compose` 로 **병행**하는 것이 일반적입니다.

---

## 5.4 동작 확인 (메트릭)

```bash
docker compose ps alloy
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:12345/
```

- Alloy UI 응답이 오면 프로세스는 기동된 것입니다.

시계열이 Prometheus에 들어왔는지는 [7번](./07-prometheus-setup.md)의 Prometheus UI **Graph**에서 `up{job="dcgm-exporter"}` 등으로 확인합니다 (6번·7번 반영·GPU 스택 기준).

---

## 5.5 설정 반영

`config.alloy` 수정 후:

```bash
docker compose restart alloy
```

---

## 참고

- [Grafana Alloy 문서](https://grafana.com/docs/alloy/latest/)
- 아키텍처 요약: [overview — Alloy 통합 수집](../../overview/01-alloy-unified-collection-architecture.md)
- Prometheus(저장·조회): [7번](./07-prometheus-setup.md) · dcgm 타깃: [6번](./06-alloy-dcgm-exporter.md)
- 로그 파이프라인: [logs/01 — Alloy 로그 수집 기능](../../logs/01-alloy-log-setup.md), [logs/02 — Loki 구축](../../logs/02-loki-setup.md)
