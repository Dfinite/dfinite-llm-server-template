# 3. dcgm-exporter 구축

GPU 서버에 dcgm-exporter를 실행 가능한 상태로 구축합니다.

## 목표

- [x] dcgm-exporter 실행 방식 결정
- [x] dcgm-exporter 정상 실행 확인 및 실행 명령어 정리
- [x] 사용 이미지·버전 정리, 컨테이너 실행 상태 확인
- [x] metrics endpoint 포트 정보 정리

---

## 3.1 실행 방식 결정

| 항목 | 결정 |
|------|------|
| 실행 형태 | Docker Compose ([`docker-compose.yml`](../../../docker-compose.yml)) |
| 구성 | `dcgm`(nv-hostengine) + `dcgm-exporter` — profile `gpu` |
| 이미지 | Docker Hub `nvidia/dcgm`, `nvidia/dcgm-exporter` |
| 연동 | exporter → hostengine `dcgm:5555` (`DCGM_REMOTE_HOSTENGINE_INFO`) |

> 공식 문서에는 dcgm-exporter 단일 컨테이너(내장 hostengine) 예도 있습니다. 본 레포는 DCGM과 exporter를 분리한 두 컨테이너 구성입니다.

---

## 3.2 사전 조건

- Linux + NVIDIA GPU + 드라이버 + NVIDIA Container Toolkit — [1번](./01-gpu-server-environment.md)
- Docker 데몬 및 `docker compose` 사용 가능
- `docker` 그룹 또는 `sudo`로 소켓 접근 가능

---

## 3.3 기동

### 확인 명령

```bash
docker compose pull dcgm dcgm-exporter
docker compose --profile gpu up -d
```

### 컨테이너 상태 확인

```bash
docker compose --profile gpu ps
```

### 결과

| 항목 | 기대 |
|------|------|
| `dcgm` | Up |
| `dcgm-exporter` | Up |

> 실패 시 `docker logs dcgm`, `docker logs dcgm-exporter`로 원인을 확인합니다. 이미지 pull 504 등은 재시도·네트워크를 확인합니다.

---

## 3.4 중지

```bash
docker compose --profile gpu down
```

> Alloy·Prometheus·Grafana를 올리는 절차는 [5번](./05-alloy-setup.md), [6번](./06-alloy-dcgm-exporter.md), [7번](./07-prometheus-setup.md), [10번](./10-grafana-setup.md) 등을 참고합니다.

---

## 3.5 구축 결과 기록

| 항목 | 값 |
|------|-----|
| `dcgm` 이미지 | `nvidia/dcgm:4.5.2-1-ubuntu22.04` |
| `dcgm-exporter` 이미지 | `nvidia/dcgm-exporter:4.5.2-4.8.1-distroless` |
| 메트릭 URL (동일 호스트) | `http://127.0.0.1:9400/metrics` |
| 메트릭 포트 | `9400` (exporter), `5555` (hostengine 내부) |

---

## 완료 조건

- [x] dcgm-exporter 정상 실행, 실행 명령어 정리
- [x] 사용 이미지·버전 정리, 컨테이너 실행 상태 확인
- [x] metrics endpoint 포트 정보 정리

---

## 메모 / 이슈

| 항목 | 내용 |
|------|------|
| `docker` 권한 | 소켓 `permission denied` 이면 `sudo` 또는 `docker` 그룹. |
| 첫 pull | 레지스트리 504 등은 재시도·네트워크 확인. |

---

## 참고

- [dcgm-exporter README (Quickstart)](https://github.com/NVIDIA/dcgm-exporter)
- [NVIDIA DCGM Exporter 문서](https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/dcgm-exporter.html)
- Docker Hub: [nvidia/dcgm](https://hub.docker.com/r/nvidia/dcgm), [nvidia/dcgm-exporter](https://hub.docker.com/r/nvidia/dcgm-exporter)
