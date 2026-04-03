#!/usr/bin/env python3
"""grafana/dashboards/gpu-overview.json 생성 (Grafana 11 timeseries)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "grafana" / "dashboards" / "gpu-overview.json"

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


def panel(
    pid: int,
    title: str,
    expr: str,
    unit: str,
    legend: str,
    grid: dict,
    *,
    min_val: float | None = None,
    max_val: float | None = None,
) -> dict:
    defaults: dict = {
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
        defaults["min"] = min_val
    if max_val is not None:
        defaults["max"] = max_val

    return {
        "datasource": DS,
        "fieldConfig": {"defaults": defaults, "overrides": []},
        "gridPos": grid,
        "id": pid,
        "options": {
            "legend": {
                "calcs": [],
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True,
            },
            "tooltip": {"mode": "single", "sort": "none"},
        },
        "targets": [
            {
                "datasource": DS,
                "editorMode": "code",
                "expr": expr,
                "legendFormat": legend,
                "range": True,
                "refId": "A",
            }
        ],
        "title": title,
        "type": "timeseries",
    }


def main() -> None:
    panels = [
        panel(
            1,
            "GPU 사용률",
            "DCGM_FI_DEV_GPU_UTIL",
            "percent",
            "{{gpu}}",
            {"h": 9, "w": 12, "x": 0, "y": 0},
            min_val=0,
            max_val=100,
        ),
        panel(
            2,
            "GPU 온도",
            "DCGM_FI_DEV_GPU_TEMP",
            "celsius",
            "{{gpu}}",
            {"h": 9, "w": 12, "x": 12, "y": 0},
        ),
        panel(
            3,
            "GPU 메모리 사용량",
            "DCGM_FI_DEV_FB_USED",
            "mbytes",
            "{{gpu}}",
            {"h": 9, "w": 12, "x": 0, "y": 9},
        ),
        panel(
            4,
            "GPU 전력",
            "DCGM_FI_DEV_POWER_USAGE",
            "watt",
            "{{gpu}}",
            {"h": 9, "w": 12, "x": 12, "y": 9},
        ),
    ]

    dash = {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "10s",
        "schemaVersion": 39,
        "style": "dark",
        "tags": ["gpu", "dcgm"],
        "templating": {"list": []},
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "GPU 모니터링",
        "uid": "gpu-overview",
        "version": 1,
        "weekStart": "",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dash, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
