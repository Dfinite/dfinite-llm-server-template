# 1. 추후 고려: 컨테이너 메모리 제한

`monitoring/` 스택의 모든 컨테이너는 현재 메모리 제한이 없습니다. 메트릭·로그 급증 시 단일 컨테이너가 호스트 메모리를 독식해 다른 서비스 전체가 OOM될 수 있습니다. 단, 제한값을 잘못 설정하면 부하 스파이크 시 컨테이너가 OOM-kill되어 오히려 재시작 루프가 발생할 수 있으므로, **실측 후 단계적으로 적용**하는 것을 권장합니다.

---

## 목표

- [ ] 각 서비스의 정상 운영 중 피크 메모리 실측
- [ ] `mem_reservation`(soft limit) 먼저 적용
- [ ] 실측값 기반 `mem_limit`(hard limit) 설정

---

## 1.1 현재 상태와 위험

| 상태 | 설명 |
|------|------|
| **제한 없음 (현재)** | 메트릭·로그 급증 시 컨테이너 하나가 호스트 메모리 독식 → 다른 서비스 전체 OOM 위험 |
| **hard limit 과소 설정** | 부하 스파이크 시 OOM-kill → 재시작 루프 → 오히려 더 불안정 |
| **soft limit + hard limit 조합** | 권장. 스케줄러 힌트 + 상한선으로 안정적 운영 가능 |

---

## 1.2 서비스별 제안값 (참고)

실측 전 초기 참고값입니다. **실측 후 조정 필수.**

| 서비스 | `mem_reservation` | `mem_limit` | 핵심 근거 |
|--------|-------------------|-------------|-----------|
| prometheus | 512m | 1g | 시계열 수 × WAL 버퍼 |
| loki | 256m | 512m | 청크 캐시 + 쿼리 버퍼 |
| alloy | 128m | 256m | remote_write WAL + 스크랩 버퍼 |
| grafana | 256m | 512m | 다중 패널 동시 쿼리 |
| dcgm | 256m | 512m | GPU 드라이버 텔레메트리 버퍼 |
| dcgm-exporter | 64m | 128m | 경량 exporter, 자체 상태 없음 |

---

## 1.3 적용 방법

### 실측 먼저

```bash
docker stats --no-stream
```

정상 운영 중 피크 메모리를 충분히 관측한 후 그 값의 **1.5~2배**를 `mem_limit`으로 설정.

### docker-compose.yml 적용 형식

```yaml
services:
  prometheus:
    deploy:
      resources:
        reservations:
          memory: 512m   # soft limit — 보장값, 초과 가능
        limits:
          memory: 1g     # hard limit — 이 이상은 OOM-kill
```

---

## 1.4 적용 순서 (권장)

| 단계 | 내용 |
|------|------|
| 1 | `docker stats` 로 1주일 이상 피크 메모리 관측 |
| 2 | 실측 피크의 1.5~2배를 `mem_reservation`으로 설정 |
| 3 | 안정 확인 후 `mem_limit` 추가 |
| 4 | 부하 테스트로 OOM-kill 여부 검증 |

---

## 참고

| 문서 | 내용 |
|------|------|
| [docker-compose.yml](../../docker-compose.yml) | 모니터링 스택 서비스 정의 |

- [Docker 공식 — deploy.resources 스펙](https://docs.docker.com/compose/compose-file/deploy/#resources)
