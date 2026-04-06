# 10. Grafana 구축 (Docker)

GPU 메트릭 시각화를 위해 **Grafana**를 Docker로 기동합니다.  
저장소 루트 [`docker-compose.yml`](../../../docker-compose.yml)의 `grafana` 서비스를 사용합니다.

---

## 목표

- [x] Grafana 이미지 선정
- [x] Grafana 컨테이너 실행
- [x] 관리자 계정으로 UI 접속·로그인 확인

---

## 10.1 이미지

| 항목 | 값 |
|------|-----|
| 이미지 | `grafana/grafana:11.2.0` ([Docker Hub](https://hub.docker.com/r/grafana/grafana)) |
| 데이터 볼륨 | `grafana-data` (컨테이너 `/var/lib/grafana`) |

---

## 10.2 관리자 계정

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `GRAFANA_ADMIN_USER` | `admin` | 로그인 ID |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | 비밀번호 (`.env` 미사용 시) |

**권장:** 프로젝트 루트에 `.env` 생성:

```bash
cp .env.example .env
# 편집: GRAFANA_ADMIN_PASSWORD 등 변경
```

`.env`는 `.gitignore`에 포함되어 커밋되지 않습니다.

---

## 10.3 실행

`docker compose` 로 모니터링 스택과 함께 올리기:

```bash
docker compose up -d
```

Grafana만 재시작할 때:

```bash
docker compose up -d grafana
```

확인:

```bash
docker compose ps grafana
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/login
```

---

## 10.4 접속 URL

| 항목 | 값 |
|------|-----|
| UI | **http://localhost:3000** (또는 `http://<호스트>:3000`) |
| 로그인 | `.env` 또는 기본 `admin` / `admin` |


---

## 완료 조건

| 항목 | 값 |
|------|-----|
| Docker 실행 | `docker compose up -d` |
| 접속 URL | `http://<호스트>:3000` |
| 관리자 로그인 | 확인 완료 |
| 사용 이미지 태그 | `grafana/grafana:11.2.0` |

---

## 참고

| 문서 | 내용 |
|------|------|
| [GPU-07 — Prometheus 구축](./07-prometheus-setup.md) | Prometheus 저장·조회 |
| [GPU-11 — Grafana Prometheus 데이터소스](./11-grafana-prometheus-datasource.md) | Prometheus 데이터소스 설정 |

- [Grafana Docker 설치](https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/)
