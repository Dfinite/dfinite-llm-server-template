# GPU & vLLM Monitoring Dashboard

NVIDIA GPU 메트릭과 vLLM 메트릭, 컨테이너 로그를 수집·저장·시각화하는 모니터링

```
GPU → dcgm-exporter(:9400) ─┐
vLLM(:30071) ───────────────┼─scrape→ Alloy(:12345) ─remote_write→ Prometheus(:9090) ─┐
Docker logs ────────────────┘                           └─push────────→ Loki(:3100) ───┼→ Grafana(:3000)
                                                                                         ┘
```

![Grafana GPU Dashboard](src/09-grafana-gpu-dashboard.png)

## 구성 요소

| 서비스 | 이미지 | 역할 | 포트 |
|--------|--------|------|------|
| dcgm | `nvidia/dcgm:4.5.2-1-ubuntu22.04` | GPU 호스트 엔진 | 5555 |
| dcgm-exporter | `nvidia/dcgm-exporter:4.5.2-4.8.1-distroless` | GPU 메트릭 HTTP 노출 | 9400 |
| alloy | `grafana/alloy:v1.3.1` | 로그·메트릭 통합 수집, Loki/Prometheus 전달 | 12345 |
| loki | `grafana/loki:3.1.1` | 로그 저장·조회 | 3100 |
| prometheus | `prom/prometheus:v2.52.0` | 메트릭 저장·조회 (remote_write 수신) | 9090 |
| grafana | `grafana/grafana:11.2.0` | 대시보드 시각화 | 3000 |

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

## 사전 조건

- Docker, Docker Compose
- NVIDIA GPU + 드라이버
- NVIDIA Container Toolkit

## 실행

```bash
# Grafana 관리자 비밀번호 설정
cp .env.example .env
# .env 편집: GRAFANA_ADMIN_PASSWORD 변경

# 전체 스택 기동 (GPU 서버)
docker compose --profile gpu up -d

# Prometheus + Grafana만 (GPU 없는 환경)
docker compose up -d
```

## 접속

| 서비스 | URL | 기본 계정 |
|--------|-----|-----------|
| Grafana | `http://<호스트>:3000` | `.env` 또는 `admin` / `admin` |
| Prometheus | `http://<호스트>:9090` | — |
| Loki | `http://<호스트>:3100` | — |
| dcgm-exporter | `http://<호스트>:9400/metrics` | — |

Grafana 로그인 후 **Dashboards** 에서 대시보드를 확인할 수 있습니다.

- **통합 모니터링** — GPU + vLLM + 로그 전체 현황 (요약 gauge/stat 포함)
- **GPU 모니터링** — GPU 사용률·온도·메모리·전력
- **vLLM 모니터링** — 토큰 사용량·처리 속도·요청 수·응답 시간·API 환산 비용
- **로그 모니터링** — ERROR·CRITICAL(알림 대상)·WARNING(조회용)·컨테이너별 발생률

## 프로젝트 구조

```
├── docker-compose.yml              # 서비스 정의
├── alloy/config.alloy              # Alloy 수집 파이프라인
├── loki/config.yml                 # Loki 단일 바이너리 설정
├── prometheus/prometheus.yml       # Prometheus 저장/조회 설정
├── grafana/
│   ├── dashboards/
│   │   ├── gpu-overview.json              # GPU 대시보드 JSON (생성됨)
│   │   ├── vllm-overview.json             # vLLM 대시보드 JSON (생성됨)
│   │   ├── integrated-overview.json       # 통합 대시보드 JSON (생성됨)
│   │   └── log-overview.json              # 로그 대시보드 JSON (생성됨)
│   └── provisioning/
│       ├── datasources/prometheus.yaml    # Prometheus 데이터 소스
│       ├── datasources/loki.yaml          # Loki 데이터 소스
│       ├── dashboards/default.yaml        # 대시보드 자동 로드
│       └── alerting/
│           ├── log-error-rules.yaml       # 로그 알림 규칙 (Loki)
│           ├── metric-alert-rules.yaml    # 메트릭 알림 규칙 (Prometheus)
│           └── contact-points.yaml        # 수신처 예시 (주석 — 사용 채널 해제)
├── docs/
│   ├── README.md                   # 문서 전체 목차·권장 읽기 순서
│   ├── overview/                   # 전체 아키텍처 (Alloy 통합 수집)
│   ├── metrics/
│   │   ├── gpu/                    # GPU 인프라 메트릭 (01–12)
│   │   └── vllm/                   # vLLM 서비스 메트릭 (01–03)
│   ├── logs/                       # 로그 파이프라인 (01–06, 06=알림 정책)
│   ├── dashboards/                 # Grafana 대시보드 (01=통합, 02=로그)
│   └── future/                     # 추후 검토 (프로파일링·트레이스 등)
├── src/                            # 캡처 이미지
├── scripts/                        # 대시보드 JSON·문서 생성 스크립트
│   ├── build_grafana_gpu_dashboard.py
│   ├── build_grafana_vllm_dashboard.py
│   ├── build_grafana_integrated_dashboard.py
│   └── build_grafana_log_dashboard.py
├── promql/queries.json             # GPU PromQL 정의 소스
└── Makefile                        # make assets 로 전체 재생성
```

## 문서

**목차·스택 구성 요소·권장 읽기 순서**는 [`docs/README.md`](docs/README.md)에 모아 두었습니다.

| 디렉터리 | 내용 |
|----------|------|
| [`docs/overview/`](docs/overview/) | 전체 아키텍처 (Alloy 통합 수집) |
| [`docs/metrics/gpu/`](docs/metrics/gpu/) | GPU 인프라 메트릭 (01–12) |
| [`docs/metrics/vllm/`](docs/metrics/vllm/) | vLLM 서비스 메트릭 (01–03) |
| [`docs/logs/`](docs/logs/) | Loki·Alloy 구축 (로그) |
| [`docs/dashboards/`](docs/dashboards/) | 통합 Grafana 대시보드 |
| [`docs/future/`](docs/future/) | 추후 검토 (프로파일링·분산 트레이스) |
