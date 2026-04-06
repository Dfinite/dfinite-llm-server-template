# 2. 구현 완료: 모니터링 스택 — 메인 프로젝트 통합

`monitoring/`과 메인 프로젝트(vLLM 서빙)를 통합한 구현 내용을 단계별로 정리합니다.

---

## 목표

- [x] vLLM 컨테이너와 모니터링 컨테이너가 **공유 네트워크**에서 서비스명으로 통신
- [x] vLLM 서비스 추가/삭제 시 모니터링 타깃이 **Docker 레이블 기반으로 자동 반영**
- [x] `start.sh --with-monitoring` 으로 **통합 기동**
- [x] 루트 `README.md`에 모니터링 운영 방법 추가

---

## 해결된 문제

| 문제 | 원인 | 해결 방법 |
|------|------|---------|
| vLLM 타깃 하드코딩 | `alloy/config.alloy`에 `172.17.0.1:30071` 고정 | Docker 레이블 기반 `discovery.docker` 자동 발견으로 대체 |
| Docker 네트워크 분리 | 두 compose가 각자 default 네트워크 사용 | `llm-net` 공유 외부 네트워크로 컨테이너명 직접 접근 |
| 기동 분리 | `start.sh`가 모니터링 스택을 모름 | `start.sh --with-monitoring` 플래그 추가 |

---

## 설계 방향: Docker 레이블 기반 자동 발견

서비스 추가 시 `manage_compose.py`가 `alloy/config.alloy`를 건드리지 않습니다.  
대신 vLLM 컨테이너에 **레이블**을 붙이면 Alloy가 Docker 소켓으로 자동 감지합니다.

```
manage_compose.py add my-llm
    → docker-compose.yaml 재생성 (레이블 포함)
    → Alloy가 Docker 소켓으로 레이블 달린 컨테이너 자동 발견
    → alloy/config.alloy 수정 불필요
```

로그 수집에서 이미 `discovery.docker`를 사용하고 있으므로, 메트릭에도 동일 패턴을 적용합니다.

---

## 구현 단계

### Step 1 — 공유 Docker 네트워크 추가

**변경 파일**: `scripts/manage_compose.py`, `monitoring/docker-compose.yml`

두 compose가 동일한 external network `llm-net`을 참조하도록 변경합니다.

**`manage_compose.py`의 서비스 블록 생성 템플릿에 추가**:
```yaml
networks:
  llm-net:
    name: llm-net
    driver: bridge

services:
  my-llm:
    networks:
      - llm-net
```

**`monitoring/docker-compose.yml`**:
```yaml
networks:
  llm-net:
    external: true   # 메인 compose가 생성한 네트워크 참조

services:
  alloy:
    networks:
      - llm-net      # vLLM 컨테이너에 서비스명으로 접근 가능
      - default
```

> `llm-net`은 메인 compose가 먼저 기동되어야 생성됩니다.  
> 모니터링을 먼저 띄울 경우 `docker network create llm-net`으로 수동 생성.

---

### Step 2 — Docker 레이블 기반 vLLM 자동 발견

**변경 파일**: `scripts/manage_compose.py`, `monitoring/alloy/config.alloy`

#### 2-1. manage_compose.py — 서비스 블록에 레이블 추가

`build_service_block()` 에서 생성하는 compose 서비스 블록에 Alloy 발견용 레이블을 추가합니다.

```yaml
services:
  my-llm:
    labels:
      monitoring.scrape: "true"
      monitoring.port: "10071"       # 실제 서비스 포트
      monitoring.job: "vllm"
      monitoring.service: "my-llm"  # 서비스명 (Grafana 필터용)
```

#### 2-2. alloy/config.alloy — Docker 레이블 기반 scrape로 교체

기존 하드코딩 타깃 블록을 `discovery.docker` 기반으로 교체합니다.

```alloy
// 기존 (제거)
// { __address__ = "172.17.0.1:30071", job = "vllm", service = "qwen-demo" }

// 변경 후: Docker 레이블로 자동 발견
discovery.docker "vllm" {
  host = "unix:///var/run/docker.sock"
  filter {
    name   = "label"
    values = ["monitoring.scrape=true"]
  }
}

discovery.relabel "vllm" {
  targets = discovery.docker.vllm.targets
  rule {
    source_labels = ["__meta_docker_container_label_monitoring_port"]
    target_label  = "__address__"
    replacement   = "${1}"  // 컨테이너명:포트로 재조합
  }
  rule {
    source_labels = ["__meta_docker_container_label_monitoring_job"]
    target_label  = "job"
  }
  rule {
    source_labels = ["__meta_docker_container_label_monitoring_service"]
    target_label  = "service"
  }
}

prometheus.scrape "vllm" {
  targets    = discovery.relabel.vllm.output
  forward_to = [prometheus.remote_write.default.receiver]
}
```

서비스 추가 시 레이블만 달리면 Alloy가 자동으로 scrape 대상에 포함합니다.

---

### Step 3 — start.sh / stop.sh 통합

**변경 파일**: `start.sh`, `stop.sh`

`--with-monitoring` 플래그로 모니터링 스택을 함께 기동/종료합니다.

**start.sh 추가 로직**:
```bash
if [[ "$with_monitoring" == true ]]; then
    log_info "모니터링 스택 기동 중..."
    # nvidia-smi 존재 여부로 GPU 환경 자동 감지
    if command -v nvidia-smi &> /dev/null; then
        docker compose -f "$SCRIPT_DIR/monitoring/docker-compose.yml" --profile gpu up -d
    else
        docker compose -f "$SCRIPT_DIR/monitoring/docker-compose.yml" up -d
    fi
fi
```

**stop.sh 추가 로직**:
```bash
if [[ "$with_monitoring" == true ]]; then
    docker compose -f "$SCRIPT_DIR/monitoring/docker-compose.yml" down
fi
```

---

### Step 4 — 루트 README.md 업데이트

**변경 파일**: `README.md` (루트)

배포 순서에 모니터링 기동 방법을 추가합니다.

```markdown
### 8. 모니터링 (선택)

\`\`\`bash
cp monitoring/.env.example monitoring/.env
# GRAFANA_ADMIN_PASSWORD 변경

# vLLM과 함께 기동
./start.sh --with-monitoring

# 또는 별도 기동
cd monitoring && docker compose --profile gpu up -d
\`\`\`

접속: http://<호스트>:3000 (Grafana)
```

---

## 단계별 의존성

```
Step 1 (공유 네트워크)
    └── Step 2 (Docker 레이블 자동 발견) ← 네트워크 연결 후 컨테이너명 사용 가능
Step 3 (start/stop 통합)               ← Step 1과 병렬 진행 가능
    └── Step 4 (README)
```

---

## 변경 파일 요약

| 파일 | Step | 변경 내용 |
|------|------|-----------|
| `scripts/manage_compose.py` | 1, 2 | `llm-net` 네트워크 블록 + vLLM 서비스에 레이블 추가 |
| `monitoring/docker-compose.yml` | 1 | `llm-net` external network, alloy 네트워크 설정 |
| `monitoring/alloy/config.alloy` | 2 | 하드코딩 타깃 → `discovery.docker` 레이블 기반 scrape |
| `start.sh` | 3 | `--with-monitoring` 플래그, GPU 자동 감지 |
| `README.md` (루트) | 4 | 모니터링 기동 방법 추가 |

---

## 참고

| 문서 | 내용 |
|------|------|
| [개요-01 — Alloy 통합 수집](./01-alloy-unified-collection-architecture.md) | 현재 메트릭·로그 파이프라인 구조 |
| [추후-01 — 메모리 제한](../future/01-future-memory-limits.md) | 컨테이너 리소스 제한 검토 |
