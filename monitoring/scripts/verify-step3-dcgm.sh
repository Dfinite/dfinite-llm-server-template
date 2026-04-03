#!/usr/bin/env bash
# GPU 서버에서 3번(dcgm + dcgm-exporter) 기동 후 메트릭 확인.
# 사용: bash monitoring/scripts/verify-step3-dcgm.sh  (프로젝트 루트에서)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 프로젝트: $ROOT"
echo "==> docker compose --profile gpu up -d"
docker compose --profile gpu up -d

echo ""
echo "==> 컨테이너 상태"
docker compose --profile gpu ps

echo ""
echo "==> /metrics 상단 (40줄)"
curl -sS --connect-timeout 5 --max-time 30 "http://127.0.0.1:9400/metrics" | head -n 40

echo ""
echo "==> DCGM 메트릭 샘플 (있으면 출력)"
curl -sS --connect-timeout 5 --max-time 30 "http://127.0.0.1:9400/metrics" \
  | grep -E '^DCGM_FI_DEV_(GPU_UTIL|GPU_TEMP|FB_USED|POWER_USAGE)' \
  | head -n 20 || true

echo ""
echo "==> 완료. 4번(메트릭 상세 확인)은 동일 URL로 전체 스크랩 가능."
