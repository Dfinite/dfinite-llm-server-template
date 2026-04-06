# 6. Alloy — dcgm-exporter 연동

Alloy가 **dcgm-exporter**를 scrape하도록 설정하고, (선행으로 띄운 **Prometheus**가 있으면) 시계열이 저장되는지 확인합니다.

> 선행: [5번 — Alloy (메트릭)](./05-alloy-setup.md), [04번 — `/metrics` 확인](./04-dcgm-exporter-metrics-exposure.md).  
> **Prometheus(저장소)** 는 문서 순서상 **7번**에서 기동·설정합니다. `remote_write` 검증·PromQL 확인은 [7번](./07-prometheus-setup.md)과 함께 진행합니다.

| 구분 | 상태 | 설명 |
|------|------|------|
| **scrape 설정** | 레포에 반영 | [`alloy/config.alloy`](../../../alloy/config.alloy)의 `dcgm-exporter:9400` 타깃 |
| **시계열 확인** | 검증 후 | [7번](./07-prometheus-setup.md) 기동 뒤 PromQL `DCGM_FI_DEV_GPU_UTIL` 등 |

---

## 목표

- [x] [`alloy/config.alloy`](../../../alloy/config.alloy)에 dcgm-exporter scrape 타깃(`:9400`, `job=dcgm-exporter`)이 정의되어 있음을 확인한다
- [x] GPU 프로필로 dcgm-exporter가 떠 있는 상태에서 Alloy scrape·[7번](./07-prometheus-setup.md) Prometheus 적재를 확인한다
- [x] PromQL로 `DCGM_FI_DEV_GPU_UTIL` 등 GPU 시계열을 조회한다

---

## 6.1 이미 반영된 설정 (Alloy scrape target)

[`alloy/config.alloy`](../../../alloy/config.alloy):

```alloy
prometheus.scrape "metrics" {
  targets = [
    { __address__ = "dcgm-exporter:9400", job = "dcgm-exporter" },
    // ...
  ]
  forward_to = [prometheus.remote_write.default.receiver]
}
```

- **주소**: Compose 서비스명 `dcgm-exporter` (같은 `docker-compose` 기본 네트워크에서 DNS 해석)
- **포트**: **9400** (`dcgm-exporter` 기본 메트릭 포트)
- **전달**: Alloy `prometheus.remote_write`가 Prometheus 수신 API로 전달

`docker compose.yml`에서 alloy와 dcgm-exporter를 **같은 프로젝트로** 띄우면 별도 IP 없이 scrape 됩니다.

---

## 6.2 설정 반영

`alloy/config.alloy` 변경 후:

1. Alloy 재시작  
   ```bash
   docker compose restart alloy
   ```

---

## 6.3 확인 (dcgm 타깃·연동)

1. GPU 노드에서 DCGM 스택 + Alloy + Prometheus 기동:
   ```bash
   docker compose --profile gpu up -d
   docker compose up -d alloy prometheus
   ```

2. Prometheus UI에서 PromQL 확인: `http://<호스트>:9090/graph` — 자세한 역할은 [7번](./07-prometheus-setup.md).

3. **완료 시 기록**

| 항목 | 값 |
|------|-----|
| scrape target | `dcgm-exporter:9400` (Alloy 설정) |
| 메트릭 조회 | `DCGM_FI_DEV_GPU_UTIL` |
| Prometheus UI | `http://<호스트>:9090/graph` |
| 기대 상태 | 시계열 반환 (`{gpu="0"...}` 등 라벨 포함) |

---

## 6.4 GPU 스택 없이 Prometheus/Alloy만 띄운 경우

- `dcgm-exporter` 컨테이너가 없으면 Alloy가 해당 타깃을 scrape할 수 없으므로 GPU 시계열이 생성되지 않습니다.
- 완료 확인은 **03번(GPU 스택) + Alloy + Prometheus** 를 같은 Compose 프로젝트로 띄운 뒤 진행합니다.

---

## 참고

| 문서 | 내용 |
|------|------|
| [GPU-03 — DCGM·dcgm-exporter 구축](./03-dcgm-and-dcgm-exporter-setup.md) | dcgm-exporter Docker 설정 |
| [GPU-05 — Alloy 설정](./05-alloy-setup.md) | Alloy 메트릭 scrape·remote_write |
| [GPU-07 — Prometheus 구축](./07-prometheus-setup.md) | Prometheus 저장·조회 |
| [GPU-08 — GPU PromQL](./08-gpu-metrics-promql.md) | GPU PromQL 예시 |

- [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Grafana Alloy 문서](https://grafana.com/docs/alloy/latest/)
