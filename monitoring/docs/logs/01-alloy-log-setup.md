# 1. Alloy 로그 수집 기능 활성화

Alloy는 메트릭 수집([metrics/gpu/05](../metrics/gpu/05-alloy-setup.md))에서 이미 기동되어 있습니다. 본 문서는 같은 Alloy 인스턴스에서 **Docker 컨테이너 로그를 수집해 Loki로 전송**하는 로그 파이프라인 블록을 정리합니다.

> **메트릭 수집**(dcgm-exporter·vLLM·Prometheus remote_write)은 [`docs/metrics/gpu/05-alloy-setup.md`](../metrics/gpu/05-alloy-setup.md)를 따릅니다. 본 문서는 **`loki.source.docker` · `loki.process` · `loki.write`** 에 해당하는 부분만 다룹니다.

> **문서 순서**: **1 Alloy(로그) → 2 Loki → 3 Alloy·Loki 연동 확인**. 런타임에서는 `docker compose up -d` 로 `alloy`·`loki`를 함께 기동합니다.

---

## 목표

- [x] Alloy의 Docker 로그 수집 블록(`loki.source.docker`) 역할 이해
- [x] [`alloy/config.alloy`](../../alloy/config.alloy) 로그 파이프라인 설정 확인
- [x] (검증) [2번](./02-loki-setup.md)·[3번](./03-alloy-loki-integration.md)까지 반영한 뒤 Loki에서 로그가 조회되는지 확인

---

## 1.1 로그 파이프라인 블록 구성

- 경로: [`alloy/config.alloy`](../../alloy/config.alloy)

| 블록 | 역할 |
|------|------|
| `discovery.docker` | Docker 소켓에서 실행 중인 컨테이너 목록 탐색 |
| `loki.source.docker` | 탐색된 컨테이너의 로그 스트림 수집 |
| `loki.process` | 수집된 로그에 정적 라벨(`job=docker`) 추가 |
| `loki.write` | 처리된 로그를 Loki push API로 전송 |

설정 내용 (요약):

```alloy
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
}

loki.source.docker "containers" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.docker.containers.targets
  forward_to = [loki.process.docker.receiver]
}

loki.process "docker" {
  stage.static_labels {
    values = {
      job = "docker",
    }
  }
  forward_to = [loki.write.default.receiver]
}

loki.write "default" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
```

`discovery.docker`가 탐색한 컨테이너에는 `container_name`, `compose_service` 등의 라벨이 자동으로 붙습니다. 추가 라벨 가공이 필요하면 `loki.process` 내 `stage.labels` 블록으로 확장합니다.

---

## 1.2 Docker 소켓 마운트

Alloy 컨테이너가 Docker 로그를 읽으려면 호스트 소켓이 마운트되어 있어야 합니다.

| 항목 | 값 |
|------|-----|
| Compose 볼륨 | `/var/run/docker.sock:/var/run/docker.sock:ro` |
| 로그 sink | `http://loki:3100/loki/api/v1/push` |

`docker-compose.yml`의 `alloy` 서비스에 이미 반영되어 있습니다.

---

## 1.3 설정 반영

`config.alloy` 수정 후:

```bash
docker compose restart alloy
```

---

## 1.4 동작 확인

```bash
docker compose ps alloy
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:12345/
```

Alloy UI(`http://<호스트>:12345`) → **Graph** 탭에서 `loki.source.docker.containers` 컴포넌트가 정상 상태인지 확인합니다.

로그가 Loki에 수신되는지는 [3번 — Alloy·Loki 연동 확인](./03-alloy-loki-integration.md)에서 LogQL로 검증합니다.

---

## 완료 조건

| 항목 | 값 |
|------|-----|
| 설정 파일 | `alloy/config.alloy` |
| Docker 소켓 | `/var/run/docker.sock:ro` 마운트 확인 |
| Alloy UI | `http://<호스트>:12345` — `loki.source.docker` 블록 healthy |
| 로그 sink | `http://loki:3100/loki/api/v1/push` |

---

## 참고

- [Grafana Alloy — loki.source.docker](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/)
- [Grafana Alloy — loki.process](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.process/)
- [Grafana Alloy — loki.write](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.write/)
- Alloy 메트릭 파이프라인: [metrics/gpu/05](../metrics/gpu/05-alloy-setup.md)
- Loki 구축: [2번](./02-loki-setup.md) · 연동 확인: [3번](./03-alloy-loki-integration.md)
- 로그 레벨·알림 정책(ERROR 이상): [6번](./06-log-levels-and-alerting.md)
