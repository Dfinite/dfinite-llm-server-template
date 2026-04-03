# 1. GPU 서버 환경 확인

GPU 메트릭 수집을 시작하기 전, 서버에서 GPU·컨테이너 관련 환경을 확인합니다.

## 목표

- [x] NVIDIA GPU 드라이버 설치 및 동작 확인
- [x] `nvidia-smi` 정상 실행
- [x] Docker 설치 여부 확인
- [x] NVIDIA Container Toolkit 설치 여부 확인

---

## 1.1 서버·세션 정보

| 항목 | 값 |
|------|-----|
| 호스트명 | `gpuserver` |
| 확인 계정 | `dfinite` |
| 확인 일시 | 2026-03-20 (캡처 기준) |

---

## 1.2 NVIDIA 드라이버 · `nvidia-smi`

### 확인 명령

```bash
nvidia-smi
```

### 결과 요약

| 항목 | 값 |
|------|-----|
| GPU 대수 | 2 |
| GPU 모델 | NVIDIA L40S ×2 |
| Driver Version | 570.172.08 |
| CUDA Version | 12.8 |

### 캡처

캡처 파일: [`src/01-gpu-server-environment_nvidia-smi.png`](../../../src/01-gpu-server-environment_nvidia-smi.png)

---

## 1.3 Docker

### 확인 명령

```bash
docker --version
# 또는
docker version
```

### 결과

| 항목 | 값 |
|------|-----|
| Docker 설치 여부 | 예 |
| Docker Engine 버전 | 28.3.2 (`Docker version 28.3.2`) |

> **참고:** 일반 사용자는 Docker 데몬 소켓(`/var/run/docker.sock`) 접근 권한이 없을 수 있습니다. `docker run …` 등은 `sudo` 또는 `docker` 그룹 권한이 필요합니다.

---

## 1.4 NVIDIA Container Toolkit

컨테이너에서 GPU 메트릭 수집(dcgm-exporter 등)을 하려면 **NVIDIA Container Toolkit**이 설치되어 있어야 합니다. 본 계정에는 **sudo 권한이 없어** `docker run --gpus all …` 형태의 **통합 스모크 테스트는 수행하지 않았습니다.**

대신 아래 명령으로 `nvidia-container-runtime` 존재 및 버전을 확인합니다.

### 확인 명령

```bash
which nvidia-container-runtime
nvidia-container-runtime --version
```

### 결과

| 항목 | 값 |
|------|-----|
| Toolkit 설치 여부 | 예 |
| `nvidia-container-runtime` 경로 | `/usr/bin/nvidia-container-runtime` |
| NVIDIA Container Runtime 버전 | 1.17.8 |

### 명령 출력 (전문)

```text
/usr/bin/nvidia-container-runtime
NVIDIA Container Runtime version 1.17.8
commit: f202b80a9b9d0db00d9b1d73c0128c8962c55f4d
spec: 1.2.1

runc version 1.2.5
commit: v1.2.5-0-g59923ef
spec: 1.2.0
go: go1.23.7
libseccomp: 2.5.3
```

---

## 완료 조건

- [x] `nvidia-smi` 정상 실행
- [x] `nvidia-smi` 실행 결과 캡처 보관 (`src/01-gpu-server-environment_nvidia-smi.png`)
- [x] GPU 대수, Driver Version 문서에 기록
- [x] NVIDIA Container Toolkit: `nvidia-container-runtime` 경로·버전 확인

---

## 메모 / 이슈

| 항목 | 내용 |
|------|------|
| Docker 소켓 | 일반 사용자로 `docker run …` 시 `permission denied` (소켓 접근). 모니터링 스택 구축 시 `sudo` 또는 관리자에게 `docker` 그룹 부여 여부 확인. |
| GPU 컨테이너 검증 | sudo 없이는 `docker run --gpus all` 스모크 테스트 생략. 런타임 바이너리·버전으로 설치 여부만 기록. |
