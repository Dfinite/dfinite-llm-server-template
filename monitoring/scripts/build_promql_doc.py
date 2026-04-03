#!/usr/bin/env python3
"""promql/queries.json → docs/metrics/gpu/08-gpu-metrics-promql.md 생성 (표준 라이브러리만 사용)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "promql" / "queries.json"
OUT = ROOT / "docs" / "metrics" / "gpu" / "08-gpu-metrics-promql.md"


def md_table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def main() -> None:
    data = json.loads(QUERIES.read_text(encoding="utf-8"))

    lines: list[str] = [
        "<!-- 이 파일은 scripts/build_promql_doc.py가 promql/queries.json에서 생성합니다. -->",
        "<!-- 수정: promql/queries.json 편집 후 `make promql-doc` -->",
        "",
        "# 8. GPU 메트릭 PromQL 작성",
        "",
        "dcgm-exporter가 노출하는 메트릭을 대상으로, Prometheus에서 사용할 **PromQL** 예시를 정리합니다.",
        "",
        "**PromQL**은 시계열을 수집·저장하지 않고, Prometheus에 이미 들어온 데이터를 **질의**할 때 쓰는 언어입니다 (수집·저장은 06·07번).",
        "",
        "| 구분 | 담당 |",
        "|------|------|",
        "| **노출** | dcgm-exporter — 메트릭 이름·본문은 [04](./04-dcgm-exporter-metrics-exposure.md) |",
        "| **수집** | **Alloy** — [06](./06-alloy-dcgm-exporter.md) |",
        "| **저장·조회** | **Prometheus** — TSDB 저장 후 Graph/Explore에서 **PromQL**로 조회 ([07](./07-prometheus-setup.md)) |",
        "",
        "## 목표",
        "",
        "- [x] 주요 GPU 메트릭명 확정",
        "- [x] 패널별 PromQL 작성",
        "- [x] GPU별 라벨 필터링 방법 정리",
        "- [x] Prometheus Graph에서 동작 확인",
        "",
        "> 메트릭명은 [04](./04-dcgm-exporter-metrics-exposure.md)에서 실측 확인한 이름 기준. 커스텀 counter CSV를 쓰면 이름이 달라질 수 있으므로 `/metrics`에서 재확인.",
        "",
        "---",
        "",
        "## 8.1 메트릭명 (기본 프로파일)",
        "",
        "dcgm-exporter 기본 설정(`default-counters.csv`)에서 사용하는 필드입니다.",
        "",
        "| 목적 | DCGM 필드 / Prometheus 메트릭 (일반적) | 단위·비고 |",
        "|------|------------------------------------------|-----------|",
    ]

    for row in data["metrics_table"]:
        m = row["metric"]
        lines.append(f"| {row['purpose']} | `{m}` | {row['unit']} |")

    lines.extend(
        [
            "",
            "> exporter 버전·`default-counters.csv` 변경에 따라 일부가 비활성일 수 있음. `/metrics`에서 `DCGM_FI_DEV` 로 검색하여 확인.",
            "",
            "---",
            "",
            "## 8.2 GPU별 라벨",
            "",
            "dcgm-exporter는 아래 라벨로 GPU를 구분합니다 (버전에 따라 추가·이름 차이 가능).",
            "",
            "| 라벨 | 의미 |",
            "|------|------|",
        ]
    )

    for row in data["label_table"]:
        lines.append(f"| `{row['label']}` | {row['meaning']} |")

    lines.append("")
    for ex in data["label_examples"]:
        lines.extend([f"**{ex['title']}**", "", "```promql", ex["promql"], "```", ""])

    lines.extend(["---", "", "## 8.3 PromQL 예시", ""])

    for panel in data["panels"]:
        lines.extend([f"### {panel['title']}", ""])
        for block in panel["blocks"]:
            if block.get("note"):
                lines.append(block["note"])
                lines.append("")
            lines.extend(["```promql", block["promql"], "```", ""])

    lines.extend(
        [
            "---",
            "",
            "## 8.4 패널별 확정 PromQL",
            "",
            "| 패널 | PromQL |",
            "|------|--------|",
        ]
    )

    for row in data["checklist_rows"]:
        lines.append(f"| {row['panel']} | `{row['promql']}` |")

    lines.extend(
        [
            "",
            "> Grafana 대시보드 JSON: [`grafana/dashboards/gpu-overview.json`](../../../grafana/dashboards/gpu-overview.json)",
            "",
            "---",
            "",
            "## 참고",
            "",
        ]
    )

    for ref in data["references"]:
        if ref["url"].startswith("http"):
            lines.append(f"- [{ref['label']}]({ref['url']})")
        else:
            lines.append(f"- [{ref['label']}]({ref['url']})")

    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
