# 11. Grafana — Prometheus 데이터 소스

GPU·vLLM **메트릭**을 Grafana에서 쓰려면 **Prometheus**를 데이터 소스로 등록합니다. 본 레포는 provisioning으로 설정이 파일에 고정되어 있습니다.

---

## 목표

- [x] Prometheus 데이터 소스 **provisioning** 파일이 레포에 포함됨 (`grafana/provisioning/datasources/prometheus.yaml`)
- [ ] Grafana **Connections → Data sources → Prometheus** 에서 **Save & test** 성공 (실제 기동·네트워크 전제)
- [ ] Explore에서 **PromQL** 조회 동작 확인

---

## 11.1 자동 설정 (provisioning)

| 항목 | 값 |
|------|-----|
| 설정 파일 | [`grafana/provisioning/datasources/prometheus.yaml`](../../../grafana/provisioning/datasources/prometheus.yaml) |
| 데이터 소스 이름 | **Prometheus** |
| UID | `prometheus` (GPU·vLLM·통합 대시보드 JSON에서 참조) |
| URL | `http://prometheus:9090` (Compose 서비스명, 동일 네트워크) |
| 기본 소스 | `isDefault: true` |

`docker compose up -d` 후 Grafana 기동 시 자동 적용됩니다. UI에서 수동 추가할 필요 없습니다.

---

## 11.2 연결 확인

1. `http://<호스트>:3000` 로그인
2. **Connections → Data sources → Prometheus**
3. 하단 **Save & test** → **Data source is working**

Explore에서 PromQL 예: `up`, `DCGM_FI_DEV_GPU_UTIL` (GPU 스택이 떠 있을 때).

---

## 11.3 완료 조건

| 항목 | 값 |
|------|-----|
| 데이터 소스명 | Prometheus |
| URL (설정상) | `http://prometheus:9090` |
| Save & test | 검증 후 기입 |

---

## 참고

- [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Grafana Prometheus data source](https://grafana.com/docs/grafana/latest/datasources/prometheus/)
- 문서 [10 (Grafana 구축)](./10-grafana-setup.md), [12 (GPU 대시보드)](./12-gpu-grafana-dashboard.md)
