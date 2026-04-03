#!/usr/bin/env python3
"""grafana/dashboards/integrated-overview.json 생성 — GPU + vLLM 통합 대시보드."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "grafana" / "dashboards" / "integrated-overview.json"

DS = {"type": "prometheus", "uid": "prometheus"}
DS_LOKI = {"type": "loki", "uid": "loki"}


def ts_custom() -> dict:
    return {
        "axisBorderShow": False,
        "axisCenteredZero": False,
        "axisColorMode": "text",
        "axisLabel": "",
        "axisPlacement": "auto",
        "barAlignment": 0,
        "drawStyle": "line",
        "fillOpacity": 10,
        "gradientMode": "none",
        "hideFrom": {"legend": False, "tooltip": False, "viz": False},
        "lineInterpolation": "smooth",
        "lineWidth": 2,
        "pointSize": 5,
        "scaleDistribution": {"type": "linear"},
        "showPoints": "never",
        "spanNulls": False,
        "stacking": {"group": "A", "mode": "none"},
        "thresholdsStyle": {"mode": "off"},
    }


def _defaults(unit: str, *, min_val=None, max_val=None) -> dict:
    d: dict = {
        "color": {"mode": "palette-classic"},
        "custom": ts_custom(),
        "mappings": [],
        "thresholds": {
            "mode": "absolute",
            "steps": [{"color": "green", "value": None}],
        },
        "unit": unit,
    }
    if min_val is not None:
        d["min"] = min_val
    if max_val is not None:
        d["max"] = max_val
    return d


def ts_panel(
    pid: int,
    title: str,
    targets: list[dict],
    unit: str,
    grid: dict,
    *,
    min_val: float | None = None,
    max_val: float | None = None,
) -> dict:
    return {
        "datasource": DS,
        "fieldConfig": {
            "defaults": _defaults(unit, min_val=min_val, max_val=max_val),
            "overrides": [],
        },
        "gridPos": grid,
        "id": pid,
        "options": {
            "legend": {
                "calcs": ["lastNotNull"],
                "displayMode": "table",
                "placement": "right",
                "showLegend": True,
            },
            "tooltip": {"mode": "all", "sort": "desc"},
        },
        "targets": targets,
        "title": title,
        "type": "timeseries",
    }


def gauge_panel(
    pid: int,
    title: str,
    targets: list[dict],
    unit: str,
    grid: dict,
    thresholds: list[dict],
    *,
    min_val: float = 0,
    max_val: float = 100,
) -> dict:
    return {
        "datasource": DS,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": thresholds},
                "unit": unit,
                "min": min_val,
                "max": max_val,
            },
            "overrides": [],
        },
        "gridPos": grid,
        "id": pid,
        "options": {
            "minVizHeight": 75,
            "minVizWidth": 75,
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
            "sizing": "auto",
        },
        "targets": targets,
        "title": title,
        "type": "gauge",
    }


def stat_panel(
    pid: int,
    title: str,
    targets: list[dict],
    unit: str,
    grid: dict,
    thresholds: list[dict],
    *,
    graph_mode: str = "area",
) -> dict:
    return {
        "datasource": DS,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": thresholds},
                "unit": unit,
            },
            "overrides": [],
        },
        "gridPos": grid,
        "id": pid,
        "options": {
            "colorMode": "background",
            "graphMode": graph_mode,
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto",
            "wideLayout": True,
        },
        "targets": targets,
        "title": title,
        "type": "stat",
    }


def target(expr: str, legend: str, ref: str = "A") -> dict:
    return {
        "datasource": DS,
        "editorMode": "code",
        "expr": expr,
        "legendFormat": legend,
        "range": True,
        "refId": ref,
    }


def logs_panel(pid: int, title: str, targets: list[dict], grid: dict) -> dict:
    return {
        "datasource": DS_LOKI,
        "gridPos": grid,
        "id": pid,
        "options": {
            "dedupStrategy": "none",
            "enableLogDetails": True,
            "prettifyLogMessage": False,
            "showCommonLabels": False,
            "showLabels": False,
            "showTime": True,
            "sortOrder": "Descending",
            "wrapLogMessage": True,
        },
        "targets": targets,
        "title": title,
        "type": "logs",
    }


def loki_target(expr: str, ref: str = "A") -> dict:
    return {
        "datasource": DS_LOKI,
        "editorMode": "code",
        "expr": expr,
        "queryType": "range",
        "refId": ref,
    }


def loki_ts_target(expr: str, legend: str, ref: str = "A") -> dict:
    return {
        "datasource": DS_LOKI,
        "editorMode": "code",
        "expr": expr,
        "legendFormat": legend,
        "queryType": "range",
        "refId": ref,
    }


def row_panel(pid: int, title: str, y: int) -> dict:
    return {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": pid,
        "title": title,
        "type": "row",
    }


# -- API pricing (2026-03-25) --
GPT4O_IN, GPT4O_OUT = 2.5, 10.0
GEMINI_PRO_IN, GEMINI_PRO_OUT = 1.25, 10.0
GPT4O_MINI_IN, GPT4O_MINI_OUT = 0.15, 0.60
GEMINI_FLASH_IN, GEMINI_FLASH_OUT = 0.3, 2.5

TH_GREEN = [{"color": "green", "value": None}]
TH_GPU_UTIL = [
    {"color": "green", "value": None},
    {"color": "yellow", "value": 70},
    {"color": "red", "value": 90},
]
TH_TEMP = [
    {"color": "green", "value": None},
    {"color": "yellow", "value": 70},
    {"color": "red", "value": 80},  # 80°C: 스로틀링 직전 — 알림 임계값과 동일
]
TH_CACHE = [
    {"color": "green", "value": None},
    {"color": "yellow", "value": 0.7},
    {"color": "red", "value": 0.9},
]


def cost_expr(in_price: float, out_price: float) -> str:
    return (
        f'(vllm:prompt_tokens_total{{model_name=~".+"}} * {in_price} / 1e6) + '
        f'(vllm:generation_tokens_total{{model_name=~".+"}} * {out_price} / 1e6)'
    )


def main() -> None:
    panels = []
    pid = 1
    y = 0

    # ═══════════════════════════════════════════
    #  요약 (stat / gauge)
    # ═══════════════════════════════════════════
    panels.append(row_panel(pid, "요약", y)); pid += 1; y += 1

    panels.append(gauge_panel(pid, "GPU 평균 사용률", [
        target("avg(DCGM_FI_DEV_GPU_UTIL)", "avg"),
    ], "percent", {"h": 5, "w": 4, "x": 0, "y": y}, TH_GPU_UTIL))
    pid += 1

    panels.append(gauge_panel(pid, "GPU 최고 온도", [
        target("max(DCGM_FI_DEV_GPU_TEMP)", "max"),
    ], "celsius", {"h": 5, "w": 4, "x": 4, "y": y}, TH_TEMP))
    pid += 1

    panels.append(stat_panel(pid, "입력 토큰 (누적)", [
        target('vllm:prompt_tokens_total{model_name=~".+"}', "{{service}}"),
    ], "short", {"h": 5, "w": 4, "x": 8, "y": y}, TH_GREEN, graph_mode="none"))
    pid += 1

    panels.append(stat_panel(pid, "생성 토큰 (누적)", [
        target('vllm:generation_tokens_total{model_name=~".+"}', "{{service}}"),
    ], "short", {"h": 5, "w": 4, "x": 12, "y": y}, TH_GREEN, graph_mode="none"))
    pid += 1

    panels.append(stat_panel(pid, "완료 요청 수", [
        target('vllm:request_success_total{model_name=~".+"}', "{{service}}"),
    ], "short", {"h": 5, "w": 4, "x": 16, "y": y}, TH_GREEN, graph_mode="none"))
    pid += 1

    panels.append(gauge_panel(pid, "KV 캐시 사용률", [
        target('vllm:gpu_cache_usage_perc{model_name=~".+"}', "{{service}}"),
    ], "percentunit", {"h": 5, "w": 4, "x": 20, "y": y}, TH_CACHE, min_val=0, max_val=1))
    pid += 1
    y += 5

    # ═══════════════════════════════════════════
    #  GPU 메트릭
    # ═══════════════════════════════════════════
    panels.append(row_panel(pid, "GPU 메트릭 (dcgm-exporter)", y)); pid += 1; y += 1

    panels.append(ts_panel(pid, "GPU 사용률", [
        target("DCGM_FI_DEV_GPU_UTIL", "GPU {{gpu}}"),
    ], "percent", {"h": 8, "w": 12, "x": 0, "y": y}, min_val=0, max_val=100))
    pid += 1

    panels.append(ts_panel(pid, "GPU 온도", [
        target("DCGM_FI_DEV_GPU_TEMP", "GPU {{gpu}}"),
    ], "celsius", {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 8

    panels.append(ts_panel(pid, "GPU 메모리 사용량", [
        target("DCGM_FI_DEV_FB_USED", "GPU {{gpu}}"),
    ], "mbytes", {"h": 8, "w": 12, "x": 0, "y": y}))
    pid += 1

    panels.append(ts_panel(pid, "GPU 전력", [
        target("DCGM_FI_DEV_POWER_USAGE", "GPU {{gpu}}"),
    ], "watt", {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 8

    # ═══════════════════════════════════════════
    #  vLLM 메트릭
    # ═══════════════════════════════════════════
    panels.append(row_panel(pid, "vLLM 메트릭 (보조 지표)", y)); pid += 1; y += 1

    panels.append(ts_panel(pid, "토큰 사용량 (누적)", [
        target('vllm:prompt_tokens_total{model_name=~".+"}', "입력 {{service}}"),
        target('vllm:generation_tokens_total{model_name=~".+"}', "생성 {{service}}", "B"),
    ], "short", {"h": 8, "w": 12, "x": 0, "y": y}))
    pid += 1

    panels.append(ts_panel(pid, "토큰 처리 속도 (tok/s)", [
        target('rate(vllm:prompt_tokens_total{model_name=~".+"}[5m])', "입력 {{service}}"),
        target('rate(vllm:generation_tokens_total{model_name=~".+"}[5m])', "생성 {{service}}", "B"),
    ], "none", {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 8

    panels.append(ts_panel(pid, "요청 수", [
        target('vllm:request_success_total{finished_reason="stop",model_name=~".+"}', "완료 {{service}}"),
        target('vllm:request_success_total{finished_reason="length",model_name=~".+"}', "길이 초과 {{service}}", "B"),
        target('vllm:request_success_total{finished_reason="abort",model_name=~".+"}', "중단 {{service}}", "C"),
    ], "short", {"h": 8, "w": 12, "x": 0, "y": y}))
    pid += 1

    panels.append(ts_panel(pid, "평균 응답 시간", [
        target(
            'rate(vllm:e2e_request_latency_seconds_sum{model_name=~".+"}[5m]) '
            '/ rate(vllm:e2e_request_latency_seconds_count{model_name=~".+"}[5m])',
            "avg {{service}}",
        ),
    ], "s", {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 8

    # ═══════════════════════════════════════════
    #  API 환산 비용
    # ═══════════════════════════════════════════
    panels.append(row_panel(pid, "API 환산 비용 (참고, 2026-03-25 기준)", y)); pid += 1; y += 1

    panels.append(ts_panel(pid, "플래그십 모델 환산 비용 ($)", [
        target(cost_expr(GPT4O_IN, GPT4O_OUT), "GPT-4o"),
        target(cost_expr(GEMINI_PRO_IN, GEMINI_PRO_OUT), "Gemini 2.5 Pro", "B"),
    ], "currencyUSD", {"h": 8, "w": 12, "x": 0, "y": y}))
    pid += 1

    panels.append(ts_panel(pid, "경량 모델 환산 비용 ($)", [
        target(cost_expr(GPT4O_MINI_IN, GPT4O_MINI_OUT), "GPT-4o-mini"),
        target(cost_expr(GEMINI_FLASH_IN, GEMINI_FLASH_OUT), "Gemini 2.5 Flash", "B"),
    ], "currencyUSD", {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 8

    # ═══════════════════════════════════════════
    #  로그 (Loki)
    # ═══════════════════════════════════════════
    panels.append(row_panel(pid, "로그 (Loki)", y)); pid += 1; y += 1

    # 알림 대상 기준 (docs/logs/06 정책: ERROR·CRITICAL만 알림)
    panels.append(logs_panel(pid, "ERROR·CRITICAL 로그 (알림 대상)", [
        loki_target('{job="docker"} |~ "(?i)error|critical"'),
    ], {"h": 10, "w": 12, "x": 0, "y": y}))
    pid += 1

    panels.append(logs_panel(pid, "vLLM 로그", [
        loki_target('{container_name=~"vllm.*"}'),
    ], {"h": 10, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 10

    # 알림 임계값과 동일 쿼리 — 발생률 > 0 이면 알림 규칙 발화
    panels.append(ts_panel(pid, "컨테이너별 ERROR·CRITICAL 발생률 (logs/s)", [
        loki_ts_target('rate({job="docker"} |~ "(?i)error|critical" [5m])', "{{container_name}}"),
    ], "short", {"h": 8, "w": 24, "x": 0, "y": y}))
    pid += 1

    dash = {
        "annotations": {"list": []},
        "description": "GPU 인프라 메트릭 + vLLM 서비스 메트릭 + 컨테이너 로그 통합 대시보드",
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "10s",
        "schemaVersion": 39,
        "style": "dark",
        "tags": ["gpu", "vllm", "loki", "integrated"],
        "templating": {"list": []},
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "통합 모니터링",
        "uid": "integrated-overview",
        "version": 1,
        "weekStart": "",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dash, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
