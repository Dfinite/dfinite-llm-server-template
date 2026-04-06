# 5. Grafana — Loki 데이터소스

컨테이너 로그를 Grafana에서 조회하려면 **Loki**를 데이터소스로 등록합니다. 본 레포는 provisioning으로 설정이 파일에 고정되어 있습니다.

---

## 목표

- [x] Loki 데이터소스 **provisioning** 파일이 레포에 포함됨 (`grafana/provisioning/datasources/loki.yaml`)
- [ ] Grafana **Connections → Data sources → Loki** 에서 **Save & test** 성공 (실제 기동·네트워크 전제)
- [ ] Explore에서 **LogQL** 조회 동작 확인

---

## 5.1 자동 설정 (provisioning)

| 항목 | 값 |
|------|-----|
| 설정 파일 | [`grafana/provisioning/datasources/loki.yaml`](../../../grafana/provisioning/datasources/loki.yaml) |
| 데이터소스 이름 | **Loki** |
| UID | `loki` |
| URL | `http://loki:3100` (Compose 서비스명, 동일 네트워크) |

`docker compose up -d` 후 Grafana 기동 시 자동 적용됩니다. UI에서 수동 추가할 필요 없습니다.

---

## 5.2 연결 확인

1. `http://<호스트>:3000` 로그인
2. **Connections → Data sources → Loki**
3. 하단 **Save & test** → **Data source connected and labels found**

Explore에서 LogQL 예: `{job="docker"}` (Alloy가 수집 중일 때).

---

## 5.3 Explore에서 로그 조회

Grafana Explore(`http://<호스트>:3000/explore`)에서:

1. 데이터소스 드롭다운에서 **Loki** 선택
2. **Label filters** 또는 **Code** 탭에서 LogQL 직접 입력

기본 확인 쿼리:

```logql
{job="docker"}
```

컨테이너별 필터:

```logql
{container_name="prometheus"}
```

자세한 쿼리는 [04 — LogQL 쿼리 레퍼런스](./04-logql-queries.md) 참고.

Grafana 로그 전용 대시보드: **Dashboards → 로그 모니터링** (UID: `log-overview`).

---

## 완료 조건

| 항목 | 값 |
|------|-----|
| 데이터소스명 | Loki |
| URL (설정상) | `http://loki:3100` |
| Save & test | ✅ Data source connected and labels found |
| Explore LogQL | `{job="docker"}` 로그 조회 확인 |

---

## 참고

| 문서 | 내용 |
|------|------|
| [01 — Alloy 로그 수집](./01-alloy-log-setup.md) | Alloy 로그 파이프라인 설정 |
| [03 — Alloy·Loki 연동](./03-alloy-loki-integration.md) | 연동 확인 |
| [04 — LogQL 쿼리](./04-logql-queries.md) | LogQL 쿼리 레퍼런스 |
| [06 — 로그 레벨·알림 정책](./06-log-levels-and-alerting.md) | ERROR 이상 알림 정책 |
| [GPU-11 — Grafana Prometheus 데이터소스](../metrics/gpu/11-grafana-prometheus-datasource.md) | GPU·vLLM 메트릭 데이터소스 |

- [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Grafana Loki 데이터소스](https://grafana.com/docs/grafana/latest/datasources/loki/)
