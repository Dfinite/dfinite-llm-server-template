# 3. Alloy — Loki 연동 확인

Alloy가 수집한 Docker 컨테이너 로그가 **Loki에 정상 적재**되는지 확인합니다.

> 선행: [1번 — Alloy 로그 수집 기능 활성화](./01-alloy-log-setup.md), [2번 — Loki 구축](./02-loki-setup.md).

| 구분 | 담당 |
|------|------|
| **로그 수집** | Alloy — `loki.source.docker` ([01](./01-alloy-log-setup.md)) |
| **저장·조회** | Loki — push API 수신 후 TSDB 저장, LogQL 조회 |

---

## 목표

- [x] Alloy UI에서 `loki.source.docker` 컴포넌트 정상 동작 확인
- [x] Loki push API 수신 확인
- [x] Grafana Explore 또는 Loki API에서 LogQL로 로그 조회 확인

---

## 3.1 Alloy UI 확인

`http://<호스트>:12345` 접속 → **Graph** 탭에서 아래 컴포넌트가 초록색(healthy) 상태인지 확인합니다.

| 컴포넌트 | 기대 상태 |
|----------|----------|
| `discovery.docker.containers` | healthy |
| `loki.source.docker.containers` | healthy |
| `loki.process.docker` | healthy |
| `loki.write.default` | healthy |

---

## 3.2 Loki push API 확인

Loki가 push 요청을 수신하는지 직접 확인합니다.

```bash
# Loki 헬스 확인
curl -sS http://127.0.0.1:3100/ready

# 수집된 라벨 목록 조회 (로그가 적재된 경우 비어 있지 않음)
curl -sS "http://127.0.0.1:3100/loki/api/v1/labels" | jq .
```

`job`, `container_name` 등의 라벨이 반환되면 로그가 정상 적재된 것입니다.

---

## 3.3 LogQL로 로그 조회

Loki API 또는 Grafana Explore에서 아래 LogQL로 수집된 로그를 확인합니다.

```bash
# 최근 100줄 — job=docker 전체
curl -sG "http://127.0.0.1:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="docker"}' \
  --data-urlencode 'limit=100' | jq '.data.result[].stream'
```

컨테이너 이름으로 좁히기:

```bash
curl -sG "http://127.0.0.1:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={container_name="prometheus"}' \
  --data-urlencode 'limit=50' | jq '.data.result[].stream'
```

| 확인 항목 | 기대 | 비고 |
|-----------|------|------|
| `job` 라벨 | `"docker"` | `loki.process` 정적 라벨 |
| `container_name` 라벨 | 실행 중인 컨테이너명 | `discovery.docker` 자동 부여 |
| `compose_service` 라벨 | Compose 서비스명 | docker-compose 사용 시 |

---

## 3.4 라벨 구조

`discovery.docker`가 자동으로 부여하는 주요 라벨입니다.

| 라벨 | 예시 값 | 설명 |
|------|---------|------|
| `job` | `docker` | `loki.process` 정적 추가 |
| `container_name` | `prometheus` | 컨테이너 이름 |
| `compose_project` | `monitoring` | Compose 프로젝트명 |
| `compose_service` | `prometheus` | Compose 서비스명 |

---

## 완료 조건

| 항목 | 상태 |
|------|------|
| Alloy UI 컴포넌트 전체 healthy | |
| Loki `/loki/api/v1/labels` 에서 `job`, `container_name` 반환 | |
| LogQL `{job="docker"}` 로그 조회 성공 | |

---

## 참고

- [Loki HTTP API](https://grafana.com/docs/loki/latest/reference/loki-http-api/)
- [Grafana Alloy — loki.source.docker](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/)
- 문서 [01 (Alloy 로그 수집 기능 활성화)](./01-alloy-log-setup.md), [02 (Loki 구축)](./02-loki-setup.md)
- LogQL 쿼리 레퍼런스: [04 — LogQL](./04-logql-queries.md)
