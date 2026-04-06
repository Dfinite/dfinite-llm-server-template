# GPU & vLLM Monitoring

vLLM + Docker Compose 기반 LLM 서빙 템플릿에 모니터링 기능을 추가합니다.  
NVIDIA GPU 메트릭·vLLM 서비스 메트릭·컨테이너 로그를 수집하여 Grafana 대시보드로 시각화합니다.

```
GPU → dcgm-exporter(:9400) ─┐
vLLM(<서비스포트>) ──────────┼─scrape→ Alloy(:12345) ─remote_write→ Prometheus(:9090) ─┐
Docker logs ─────────────────┘                          └─push───────→ Loki(:3100) ──────┼→ Grafana(:3000)
                                                                                          ┘
```

---

## 구성 요소

| 서비스 | 이미지 | 역할 | 포트 |
|--------|--------|------|------|
| dcgm | `nvidia/dcgm:4.5.2-1-ubuntu22.04` | GPU 호스트 엔진 | 5555 |
| dcgm-exporter | `nvidia/dcgm-exporter:4.5.2-4.8.1-distroless` | GPU 메트릭 HTTP 노출 | 9400 |
| alloy | `grafana/alloy:v1.3.1` | 로그·메트릭 통합 수집, Loki/Prometheus 전달 | 12345 |
| loki | `grafana/loki:3.1.1` | 로그 저장·조회 | 3100 |
| prometheus | `prom/prometheus:v2.52.0` | 메트릭 저장·조회 (remote_write 수신) | 9090 |
| grafana | `grafana/grafana:11.2.0` | 대시보드 시각화 | 3000 |

---

## 수집 메트릭

**GPU (DCGM)**

| 메트릭 | PromQL | 단위 |
|--------|--------|------|
| GPU 사용률 | `DCGM_FI_DEV_GPU_UTIL` | % |
| GPU 온도 | `DCGM_FI_DEV_GPU_TEMP` | °C |
| GPU 메모리 사용량 | `DCGM_FI_DEV_FB_USED` | MiB |
| GPU 전력 | `DCGM_FI_DEV_POWER_USAGE` | W |

**vLLM**

| 메트릭 | PromQL | 설명 |
|--------|--------|------|
| 토큰 사용량 (누적) | `vllm:prompt_tokens_total`, `vllm:generation_tokens_total` | 입력·생성 토큰 누적 수 |
| 토큰 처리 속도 | `rate(vllm:prompt_tokens_total[5m])` | tok/s |
| 요청 수 | `vllm:request_success_total` | 완료 요청 건수 (stop/length/abort) |
| 평균 응답 시간 | `rate(vllm:e2e_request_latency_seconds_sum[5m]) / rate(...count[5m])` | 초 단위 |

---

## 사전 조건

- Docker, Docker Compose
- NVIDIA GPU + 드라이버
- NVIDIA Container Toolkit

---

## vLLM 서비스 연동

`manage_compose.py`로 서비스를 등록하면 **자동으로 연동**됩니다. `alloy/config.alloy`를 직접 수정할 필요가 없습니다.

`manage_compose.py add` 실행 시 생성된 vLLM 컨테이너에 아래 레이블이 자동으로 붙습니다:

```yaml
labels:
  monitoring.scrape: "true"
  monitoring.port: "<서비스포트>"
  monitoring.job: "vllm"
  monitoring.service: "<서비스명>"
```

Alloy는 Docker 소켓으로 이 레이블이 달린 컨테이너를 자동 감지하여 scrape 대상에 포함합니다. 서비스를 추가하거나 삭제해도 모니터링 설정 변경 없이 자동 반영됩니다.

두 스택은 `llm-net` Docker 네트워크를 공유하므로 Alloy가 컨테이너명으로 vLLM에 직접 접근합니다.

---

## 실행

**1. 환경 변수 설정**

```bash
cd monitoring
cp .env.example .env
# .env 편집: GRAFANA_ADMIN_PASSWORD 변경
```

**2. 모니터링 스택 기동**

```bash
# GPU 서버 (dcgm + dcgm-exporter 포함)
docker compose --profile gpu up -d

# GPU 없는 환경 (Prometheus + Grafana + Alloy + Loki만)
docker compose up -d
```

**3. 메인 프로젝트와 함께 운영할 때**

모니터링 스택은 메인 프로젝트와 독립적으로 기동합니다. 순서는 무관합니다.

```bash
# 프로젝트 루트에서 vLLM 서비스 시작
cd ..
./start.sh

# monitoring 디렉터리에서 모니터링 시작
cd monitoring
docker compose --profile gpu up -d
```

---

## 접속

| 서비스 | URL | 기본 계정 |
|--------|-----|-----------|
| Grafana | `http://<호스트>:3000` | `.env` 또는 `admin` / `admin` |
| Prometheus | `http://<호스트>:9090` | — |
| Loki | `http://<호스트>:3100` | — |
| dcgm-exporter | `http://<호스트>:9400/metrics` | — |

Grafana 로그인 후 **Dashboards** 에서 대시보드를 확인할 수 있습니다.

| 대시보드 | 내용 |
|----------|------|
| **통합 모니터링** | GPU + vLLM + 로그 전체 현황 (요약 gauge/stat 포함) |
| **GPU 모니터링** | GPU 사용률·온도·메모리·전력 |
| **vLLM 모니터링** | 토큰 사용량·처리 속도·요청 수·응답 시간·API 환산 비용 |
| **로그 모니터링** | ERROR·CRITICAL(알림 대상)·WARNING(조회용)·컨테이너별 발생률 |

---

## 프로젝트 구조

```
monitoring/
├── docker-compose.yml              # 서비스 정의 (healthcheck 포함)
├── alloy/config.alloy              # Alloy 수집 파이프라인 (vLLM 타깃 포트 수정 필요)
├── loki/config.yml                 # Loki 단일 바이너리 설정
├── prometheus/prometheus.yml       # Prometheus 저장/조회 설정
├── grafana/
│   ├── dashboards/                 # 대시보드 JSON (scripts/로 생성)
│   │   ├── gpu-overview.json
│   │   ├── vllm-overview.json
│   │   ├── integrated-overview.json
│   │   └── log-overview.json
│   └── provisioning/
│       ├── datasources/            # Prometheus·Loki 데이터소스 자동 등록
│       ├── dashboards/             # 대시보드 자동 로드 설정
│       └── alerting/               # 알림 규칙·수신처 (contact-points.yaml 편집 필요)
├── docs/                           # 구축 문서 (docs/README.md 참고)
├── scripts/                        # 대시보드 JSON·문서 생성 스크립트
├── promql/queries.json             # GPU PromQL 정의 소스
└── Makefile                        # make assets 로 전체 재생성
```

---

## 알림 설정

기본적으로 알림 rule은 활성화되어 있으나 **수신처(contact point)는 비활성** 상태입니다.

```bash
# Slack, 이메일 등 수신처 설정
vi grafana/provisioning/alerting/contact-points.yaml
docker compose restart grafana
```

---

## 대시보드 재생성

대시보드 JSON을 수정하거나 새로 생성할 때:

```bash
make assets              # 전체 재생성
make grafana-dashboard   # GPU 대시보드만
make grafana-vllm-dashboard
make grafana-integrated-dashboard
make grafana-log-dashboard
```

변경 후 반영:

```bash
docker compose restart grafana
```

---

## 문서

구축 과정·설계 결정·PromQL 레퍼런스는 [`docs/README.md`](docs/README.md) 를 참고하세요.

| 디렉터리 | 내용 |
|----------|------|
| [`docs/overview/`](docs/overview/) | 전체 아키텍처 (Alloy 통합 수집) |
| [`docs/metrics/gpu/`](docs/metrics/gpu/) | GPU 인프라 메트릭 (01–12) |
| [`docs/metrics/vllm/`](docs/metrics/vllm/) | vLLM 서비스 메트릭 (01–03) |
| [`docs/logs/`](docs/logs/) | 로그 파이프라인·알림 정책 (01–07) |
| [`docs/dashboards/`](docs/dashboards/) | Grafana 대시보드 구성 |
| [`docs/future/`](docs/future/) | 추후 검토 (메모리 제한·프로파일링·분산 트레이스) |
