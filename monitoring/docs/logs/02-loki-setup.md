# 2. Loki 구축 (Docker)

컨테이너·애플리케이션 로그를 **저장·조회**하기 위해 **Grafana Loki**를 Docker로 기동합니다.  
저장소 루트 [`docker-compose.yml`](../../docker-compose.yml)에 `loki` 서비스가 포함되어 있습니다.

---

## 목표

- [x] Loki 이미지·포트·[`loki/config.yml`](../../loki/config.yml) 경로 파악
- [x] `loki/config.yml` 역할 이해 및 설정 확인
- [x] Docker Compose로 기동 후 `/ready`로 동작 확인

---

## 2.1 이미지·포트

| 항목 | 값 |
|------|-----|
| 이미지 | `grafana/loki:3.1.1` |
| HTTP | `3100` (`http_listen_port`) |
| 설정 파일 (컨테이너) | `/etc/loki/config.yml` |
| 데이터 볼륨 | `loki-data` → `/loki` |

---

## 2.2 설정 파일

- 경로: [`loki/config.yml`](../../loki/config.yml)

| 항목 | 값 | 설명 |
|------|-----|------|
| `auth_enabled` | `false` | 로컬·내부망 전제 (프로덕션에서는 인증·TLS 검토) |
| `server.http_listen_port` | `3100` | HTTP API 포트 |
| `schema_config.store` | `tsdb` | 인덱스 스토리지 엔진 |
| `schema_config.object_store` | `filesystem` | 청크를 로컬 파일시스템에 저장 |
| `limits_config.allow_structured_metadata` | `false` | 단일 노드 단순 구성 호환 |

설정 변경 후:

```bash
docker compose restart loki
```

---

## 2.3 실행

`monitoring/` 디렉터리에서:

```bash
docker compose up -d loki
```

전체 모니터링 스택과 함께:

```bash
docker compose up -d
```

---

## 2.4 동작 확인

```bash
docker compose ps loki
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3100/ready
```

`200` 응답이면 준비 완료입니다.

---

## 완료 조건

| 항목 | 값 |
|------|-----|
| 설정 파일 | `loki/config.yml` |
| 실행 명령 | `docker compose up -d loki` |
| 접속 URL | `http://<호스트>:3100` |
| Ready 확인 | `GET /ready` → HTTP 200 |

---

## 참고

| 문서 | 내용 |
|------|------|
| [01 — Alloy 로그 수집](./01-alloy-log-setup.md) | Alloy 로그 파이프라인 설정 |
| [03 — Alloy·Loki 연동](./03-alloy-loki-integration.md) | 연동 확인 |
| [개요-01 — Alloy 통합 수집](../overview/01-alloy-unified-collection-architecture.md) | 아키텍처 요약 |

- [Loki Docker 설치](https://grafana.com/docs/loki/latest/setup/install/docker/)
