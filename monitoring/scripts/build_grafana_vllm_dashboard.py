#!/usr/bin/env python3
"""grafana/dashboards/vllm-overview.json 생성 (Grafana 11 timeseries + stat)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "grafana" / "dashboards" / "vllm-overview.json"

DS = {"type": "prometheus", "uid": "prometheus"}


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
        "lineInterpolation": "linear",
        "lineWidth": 1,
        "pointSize": 5,
        "scaleDistribution": {"type": "linear"},
        "showPoints": "auto",
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
                "placement": "bottom",
                "showLegend": True,
            },
            "tooltip": {"mode": "single", "sort": "none"},
        },
        "targets": targets,
        "title": title,
        "type": "timeseries",
    }


def stat_panel(
    pid: int,
    title: str,
    targets: list[dict],
    unit: str,
    grid: dict,
    *,
    color_mode: str = "value",
    graph_mode: str = "area",
) -> dict:
    return {
        "datasource": DS,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 5},
                        {"color": "red", "value": 10},
                    ],
                },
                "unit": unit,
            },
            "overrides": [],
        },
        "gridPos": grid,
        "id": pid,
        "options": {
            "colorMode": color_mode,
            "graphMode": graph_mode,
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False,
            },
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


def row_panel(pid: int, title: str, y: int) -> dict:
    return {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": pid,
        "title": title,
        "type": "row",
    }


# -- pricing constants (2026-03-25) --
# flagship
GPT4O_IN = 2.5
GPT4O_OUT = 10.0
GEMINI_PRO_IN = 1.25
GEMINI_PRO_OUT = 10.0
# lightweight
GPT4O_MINI_IN = 0.15
GPT4O_MINI_OUT = 0.60
GEMINI_FLASH_IN = 0.3
GEMINI_FLASH_OUT = 2.5


def main() -> None:
    panels = []
    pid = 1
    y = 0

    # ── 1) 토큰 사용량 누적 ──
    panels.append(ts_panel(pid, "토큰 사용량 (누적)", [
        target('vllm:prompt_tokens_total{model_name=~".+"}', "입력 {{service}}"),
        target('vllm:generation_tokens_total{model_name=~".+"}', "생성 {{service}}", "B"),
    ], "none", {"h": 8, "w": 12, "x": 0, "y": y}))
    pid += 1

    # ── 2) 토큰 처리 속도 ──
    panels.append(ts_panel(pid, "토큰 처리 속도 (tok/s)", [
        target('rate(vllm:prompt_tokens_total{model_name=~".+"}[5m])', "입력 {{service}}"),
        target('rate(vllm:generation_tokens_total{model_name=~".+"}[5m])', "생성 {{service}}", "B"),
    ], "none", {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 8

    # ── 3) 요청 수 ──
    panels.append(ts_panel(pid, "요청 수", [
        target('vllm:request_success_total{finished_reason="stop",model_name=~".+"}', "완료 {{service}}"),
        target('vllm:request_success_total{finished_reason="length",model_name=~".+"}', "길이 초과 {{service}}", "B"),
        target('vllm:request_success_total{finished_reason="abort",model_name=~".+"}', "중단 {{service}}", "C"),
    ], "none", {"h": 8, "w": 12, "x": 0, "y": y}))
    pid += 1

    # ── 4) 평균 응답 시간 ──
    panels.append(ts_panel(pid, "평균 응답 시간", [
        target(
            'rate(vllm:e2e_request_latency_seconds_sum{model_name=~".+"}[5m]) '
            '/ rate(vllm:e2e_request_latency_seconds_count{model_name=~".+"}[5m])',
            "avg {{service}}",
        ),
    ], "s", {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 8

    # ── 5) API 환산 비용 ──
    panels.append(row_panel(pid, "API 환산 비용 (참고, 2026-03-25 기준)", y)); pid += 1; y += 1

    def cost_expr(in_price: float, out_price: float) -> str:
        return (
            f"(vllm:prompt_tokens_total{{model_name=~\".+\"}} * {in_price} / 1e6) + "
            f"(vllm:generation_tokens_total{{model_name=~\".+\"}} * {out_price} / 1e6)"
        )

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

    dash = {
        "annotations": {"list": []},
        "description": "vLLM 서비스 메트릭 대시보드 — 토큰 사용량, 요청 상태, 레이턴시, API 환산 비용 (2026-03-25 기준)",
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
        "tags": ["vllm", "llm"],
        "templating": {"list": []},
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "vLLM 모니터링",
        "uid": "vllm-overview",
        "version": 1,
        "weekStart": "",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dash, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
