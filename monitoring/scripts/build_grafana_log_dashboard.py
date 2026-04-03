#!/usr/bin/env python3
"""grafana/dashboards/log-overview.json 생성 — 컨테이너 로그 대시보드.

알림 정책 (docs/logs/06-log-levels-and-alerting.md):
  - ERROR·CRITICAL: 알림 대상
  - WARNING: 조회·모니터링 용도, 알림 대상 아님
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "grafana" / "dashboards" / "log-overview.json"

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
        "lineInterpolation": "linear",
        "lineWidth": 1,
        "pointSize": 5,
        "scaleDistribution": {"type": "linear"},
        "showPoints": "auto",
        "spanNulls": False,
        "stacking": {"group": "A", "mode": "none"},
        "thresholdsStyle": {"mode": "off"},
    }


def stat_panel(pid: int, title: str, targets: list[dict], unit: str, grid: dict) -> dict:
    return {
        "datasource": DS_LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}],
                },
                "unit": unit,
            },
            "overrides": [],
        },
        "gridPos": grid,
        "id": pid,
        "options": {
            "colorMode": "value",
            "graphMode": "area",
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


def ts_panel(pid: int, title: str, targets: list[dict], grid: dict) -> dict:
    return {
        "datasource": DS_LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": ts_custom(),
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}],
                },
                "unit": "short",
            },
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
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
        "targets": targets,
        "title": title,
        "type": "timeseries",
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


def row_panel(pid: int, title: str, y: int) -> dict:
    return {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": pid,
        "title": title,
        "type": "row",
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


def main() -> None:
    panels = []
    pid = 1
    y = 0

    # ── 요약 (stat) ──────────────────────────────────────────────────────
    panels.append(row_panel(pid, "요약", y)); pid += 1; y += 1

    panels.append(stat_panel(pid, "전체 로그 발생률 (logs/s)", [
        loki_ts_target('sum(rate({job="docker"}[5m]))', "전체"),
    ], "short", {"h": 4, "w": 8, "x": 0, "y": y}))
    pid += 1

    # ERROR·CRITICAL 발생률 — 알림 대상 기준 (docs/logs/06)
    panels.append(stat_panel(pid, "ERROR·CRITICAL 발생률 (logs/s)", [
        loki_ts_target('sum(rate({job="docker"} |~ "(?i)error|critical" [5m]))', "ERROR·CRITICAL"),
    ], "short", {"h": 4, "w": 8, "x": 8, "y": y}))
    pid += 1

    panels.append(stat_panel(pid, "vLLM 로그 발생률 (logs/s)", [
        loki_ts_target('sum(rate({container_name=~"vllm.*"}[5m]))', "vLLM"),
    ], "short", {"h": 4, "w": 8, "x": 16, "y": y}))
    pid += 1
    y += 4

    # ── 로그 스트림 ────────────────────────────────────────────────────────
    panels.append(row_panel(pid, "로그 스트림", y)); pid += 1; y += 1

    # 알림 대상: ERROR·CRITICAL (docs/logs/06 정책)
    panels.append(logs_panel(pid, "ERROR·CRITICAL 로그 (알림 대상)", [
        loki_target('{job="docker"} |~ "(?i)error|critical"'),
    ], {"h": 10, "w": 12, "x": 0, "y": y}))
    pid += 1

    # 조회용: WARNING 이상 전체
    panels.append(logs_panel(pid, "WARNING 이상 로그 (조회용)", [
        loki_target('{job="docker"} |~ "(?i)warning|error|critical"'),
    ], {"h": 10, "w": 12, "x": 12, "y": y}))
    pid += 1
    y += 10

    panels.append(logs_panel(pid, "vLLM 로그 스트림", [
        loki_target('{container_name=~"vllm.*"}'),
    ], {"h": 10, "w": 24, "x": 0, "y": y}))
    pid += 1
    y += 10

    # ── 발생률 추이 ───────────────────────────────────────────────────────
    panels.append(row_panel(pid, "발생률 추이", y)); pid += 1; y += 1

    panels.append(ts_panel(pid, "컨테이너별 전체 로그 발생률 (logs/s)", [
        loki_ts_target('rate({job="docker"}[5m])', "{{container_name}}"),
    ], {"h": 8, "w": 12, "x": 0, "y": y}))
    pid += 1

    # ERROR·CRITICAL 발생률 — 알림 임계값(> 0) 기준과 동일한 쿼리
    panels.append(ts_panel(pid, "컨테이너별 ERROR·CRITICAL 발생률 (logs/s)", [
        loki_ts_target('rate({job="docker"} |~ "(?i)error|critical" [5m])', "{{container_name}}"),
    ], {"h": 8, "w": 12, "x": 12, "y": y}))
    pid += 1

    dash = {
        "annotations": {"list": []},
        "description": "컨테이너 로그 대시보드 — ERROR·CRITICAL(알림 대상)·WARNING(조회용)·발생률 추이 (정책: docs/logs/06)",
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 39,
        "style": "dark",
        "tags": ["loki", "logs"],
        "templating": {"list": []},
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "로그 모니터링",
        "uid": "log-overview",
        "version": 1,
        "weekStart": "",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dash, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
