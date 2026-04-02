#!/usr/bin/env python3
"""
Docker Compose 서비스 관리 스크립트
services.json 레지스트리 기반으로 docker-compose.yaml을 동적 생성합니다.

Usage:
    ./scripts/manage_compose.py add <type> <config_name> [--name NAME] [--port PORT] [--gpu DEVICES]
    ./scripts/manage_compose.py remove <service_name>
    ./scripts/manage_compose.py list
    ./scripts/manage_compose.py init
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

# ── 경로 설정 ──
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
REGISTRY_PATH = PROJECT_ROOT / "services.json"
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yaml"

# parse_config.py import
sys.path.insert(0, str(SCRIPT_DIR))
from parse_config import parse_config


# ══════════════════════════════════════════════════════════════
# 레지스트리 I/O
# ══════════════════════════════════════════════════════════════

def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"services": {}}


def save_registry(registry: dict):
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, REGISTRY_PATH)


# ══════════════════════════════════════════════════════════════
# Config 로드
# ══════════════════════════════════════════════════════════════

def load_config(service_type: str, config_name: str) -> dict:
    config_path = CONFIGS_DIR / service_type / f"{config_name}.yaml"
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        available = list((CONFIGS_DIR / service_type).glob("*.yaml"))
        if available:
            print(f"Available configs:")
            for p in sorted(available):
                print(f"  {p.stem}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_config_path(service_type: str, config_name: str) -> Path:
    return CONFIGS_DIR / service_type / f"{config_name}.yaml"


# ══════════════════════════════════════════════════════════════
# 포트 관리
# ══════════════════════════════════════════════════════════════

def get_used_ports(registry: dict) -> set:
    return {svc["port"] for svc in registry["services"].values()}


# 타입별 기본 포트
DEFAULT_PORTS = {
    "chat": 10071,
    "vlm": 10071,
    "reranker": 10072,
    "embedding": 10073,
}


def resolve_port(requested: int | None, service_type: str, registry: dict) -> int:
    used = get_used_ports(registry)
    type_default = DEFAULT_PORTS.get(service_type, 10071)
    if requested is not None:
        if requested in used:
            print(f"ERROR: Port {requested} already in use")
            for name, svc in registry["services"].items():
                if svc["port"] == requested:
                    print(f"  → used by '{name}' ({svc['type']}/{svc['config']})")
            sys.exit(1)
        return requested
    if type_default not in used:
        return type_default
    candidate = type_default
    while candidate in used:
        candidate += 1
    return candidate


# ══════════════════════════════════════════════════════════════
# 서비스 블록 빌드
# ══════════════════════════════════════════════════════════════

def build_service_block(name: str, service_type: str, config_name: str,
                        port: int, gpu: str) -> str:
    """config를 parse_config로 파싱하여 서비스 블록 생성"""
    config_path = get_config_path(service_type, config_name)
    cfg = load_config(service_type, config_name)
    env_result = parse_config(str(config_path), port=port)

    cmd_args = env_result["VLLM_CMD_ARGS"]

    model_desc = cfg.get("model", {}).get("description", config_name)
    vllm_cfg = cfg.get("vllm", {})
    env_vars = vllm_cfg.get("env", {})

    # 서비스 타입별 설정
    is_chat = service_type == "chat"
    start_period = "300s" if is_chat else "120s"

    # 환경변수 라인
    env_lines = []
    env_lines.append(f"      - NVIDIA_VISIBLE_DEVICES={gpu}")
    env_lines.append(f"      - HF_TOKEN=${{HF_TOKEN:-}}")
    if is_chat:
        env_lines.append(f"      - NCCL_IB_DISABLE=1")
        env_lines.append(f"      - NCCL_P2P_DISABLE=0")
    for k, v in env_vars.items():
        env_lines.append(f"      - {k}={v}")
    env_block = "\n".join(env_lines)

    # command를 여러 줄로 포맷팅
    cmd_formatted = format_command(cmd_args)

    # GPU count
    gpu_count = "all" if gpu == "all" else 1

    block = f"""  # ─── {model_desc} ───
  {name}:
    image: vllm/vllm-openai:${{VLLM_IMAGE_TAG:-v0.18.0}}
    container_name: vllm-{name}
    ports:
      - "{port}:{port}"
    volumes:
      - ${{HF_CACHE:-~/.cache/huggingface}}:/root/.cache/huggingface
    environment:
{env_block}
    ipc: host
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:{port}/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: {start_period}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: {gpu_count}
              capabilities: [gpu]
    command: >-
{cmd_formatted}
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
"""
    return block


def format_command(cmd_args: str) -> str:
    """vLLM 명령어를 여러 줄로 포맷팅"""
    parts = cmd_args.split()
    lines = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if part.startswith("--") and i + 1 < len(parts) and not parts[i + 1].startswith("--"):
            lines.append(f"      {part} {parts[i + 1]}")
            i += 2
        else:
            lines.append(f"      {part}")
            i += 1
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# docker-compose.yaml 생성
# ══════════════════════════════════════════════════════════════

COMPOSE_HEADER = """\
# ═══════════════════════════════════════════════════════════════
# vLLM API Server — Docker Compose
# ═══════════════════════════════════════════════════════════════
# Auto-generated by scripts/manage_compose.py
# 직접 수정하지 마세요 — manage_compose.py로 관리하세요.
#
# 서비스 추가: ./scripts/manage_compose.py add <type> <config> --name <name>
# 서비스 삭제: ./scripts/manage_compose.py remove <name>
# 서비스 목록: ./scripts/manage_compose.py list
# ═══════════════════════════════════════════════════════════════

services:

"""


def generate_compose(registry: dict) -> str:
    """레지스트리 기반으로 docker-compose.yaml 전체 생성"""
    output = COMPOSE_HEADER

    if not registry["services"]:
        output += "  {} # no services\n"
        return output

    for name, svc in registry["services"].items():
        block = build_service_block(
            name=name,
            service_type=svc["type"],
            config_name=svc["config"],
            port=svc["port"],
            gpu=svc.get("gpu", "all"),
        )
        output += block + "\n"

    return output


def stop_existing_services():
    """기존 compose 서비스 종료 (compose 재생성 전 호출)"""
    if not COMPOSE_PATH.exists():
        return
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_PATH), "ps", "-q"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        if result.stdout.strip():
            print("Stopping existing services...")
            subprocess.run(
                ["docker", "compose", "-f", str(COMPOSE_PATH), "down", "--remove-orphans"],
                cwd=str(PROJECT_ROOT),
            )
    except FileNotFoundError:
        pass  # docker not installed (dev machine)


def write_compose(registry: dict):
    """docker-compose.yaml 재생성"""
    content = generate_compose(registry)
    tmp = COMPOSE_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, COMPOSE_PATH)


# ══════════════════════════════════════════════════════════════
# 명령어 핸들러
# ══════════════════════════════════════════════════════════════

def cmd_add(args):
    registry = load_registry()

    # 서비스명 결정
    name = args.name or f"{args.type}-{args.config_name}"
    if name in registry["services"]:
        print(f"ERROR: Service '{name}' already exists. Use a different --name or remove it first.")
        sys.exit(1)

    # config 존재 확인
    load_config(args.type, args.config_name)

    # 포트 결정 (타입별 기본값)
    port = resolve_port(args.port, args.type, registry)

    # GPU
    gpu = args.gpu or "all"

    # 레지스트리에 추가
    registry["services"][name] = {
        "type": args.type,
        "config": args.config_name,
        "port": port,
        "gpu": gpu,
    }

    # docker-compose.yaml 재생성
    save_registry(registry)
    write_compose(registry)

    print(f"Added service '{name}'")
    print(f"  Type:   {args.type}")
    print(f"  Config: {args.config_name}")
    print(f"  Port:   {port}")
    print(f"  GPU:    {gpu}")


def cmd_remove(args):
    registry = load_registry()
    name = args.service_name

    if name not in registry["services"]:
        print(f"ERROR: Service '{name}' not found.")
        print(f"Available services:")
        for n in registry["services"]:
            print(f"  {n}")
        sys.exit(1)

    svc = registry["services"].pop(name)

    save_registry(registry)
    write_compose(registry)

    print(f"Removed service '{name}' ({svc['type']}/{svc['config']}, port {svc['port']})")


def cmd_list(args):
    registry = load_registry()

    if not registry["services"]:
        print("No services registered.")
        print("Run './scripts/manage_compose.py init' or add services with 'add'.")
        return

    # 헤더
    print(f"{'NAME':<25} {'TYPE':<12} {'CONFIG':<25} {'PORT':<8} {'GPU'}")
    print("─" * 80)

    for name, svc in registry["services"].items():
        print(f"{name:<25} {svc['type']:<12} {svc['config']:<25} {svc['port']:<8} {svc.get('gpu', 'all')}")


def cmd_init(args):
    """기존 서비스 구성을 services.json으로 마이그레이션"""
    if REGISTRY_PATH.exists():
        print(f"WARNING: {REGISTRY_PATH} already exists.")
        confirm = input("Overwrite? (y/N): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

    registry = {"services": {}}

    print("Available configs to register:")
    print("")

    # 각 타입별 config 탐색
    for service_type in ["chat", "vlm", "reranker", "embedding"]:
        type_dir = CONFIGS_DIR / service_type
        if not type_dir.exists():
            continue
        default_port = DEFAULT_PORTS.get(service_type, 10071)
        for config_file in sorted(type_dir.glob("*.yaml")):
            config_name = config_file.stem
            print(f"  [{service_type}] {config_name} (default port {default_port})")

    print("")
    print("Enter services to register (one per line, format: TYPE CONFIG_NAME SERVICE_NAME [PORT] [GPU])")
    print("Example: chat qwen3-32b-awq my-llm 10071 all")
    print("Empty line to finish.")
    print("")

    while True:
        line = input("> ").strip()
        if not line:
            break
        parts = line.split()
        if len(parts) < 3:
            print("  ERROR: Need at least: TYPE CONFIG_NAME SERVICE_NAME")
            continue

        stype, config_name, svc_name = parts[0], parts[1], parts[2]
        port = int(parts[3]) if len(parts) > 3 else None
        gpu = parts[4] if len(parts) > 4 else "all"

        # 검증
        config_path = CONFIGS_DIR / stype / f"{config_name}.yaml"
        if not config_path.exists():
            print(f"  ERROR: Config not found: {config_path}")
            continue
        if svc_name in registry["services"]:
            print(f"  ERROR: Service name '{svc_name}' already used")
            continue

        # 포트 결정
        if port is None:
            port = DEFAULT_PORTS.get(stype, 10071)
        port = resolve_port(None if port in get_used_ports(registry) else port, stype, registry)

        registry["services"][svc_name] = {
            "type": stype,
            "config": config_name,
            "port": port,
            "gpu": gpu,
        }
        print(f"  ✓ {svc_name} ({stype}/{config_name}, port {port})")

    if not registry["services"]:
        print("No services registered.")
        return

    stop_existing_services()
    save_registry(registry)
    write_compose(registry)
    print("")
    print(f"Saved {len(registry['services'])} service(s)")
    print(f"  Registry:       {REGISTRY_PATH}")
    print(f"  Docker Compose: {COMPOSE_PATH}")


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="manage_compose",
        description="Docker Compose 서비스 동적 관리",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    add_p = sub.add_parser("add", help="서비스 추가")
    add_p.add_argument("type", choices=["chat", "reranker", "embedding"], help="서비스 타입")
    add_p.add_argument("config_name", help="Config 파일명 (확장자 제외)")
    add_p.add_argument("--name", default=None, help="서비스명 (기본: {type}-{config_name})")
    add_p.add_argument("--port", type=int, default=None, help="포트 (기본: config에서 읽기)")
    add_p.add_argument("--gpu", default=None, help="GPU 디바이스 (기본: all)")

    # remove
    rm_p = sub.add_parser("remove", help="서비스 삭제")
    rm_p.add_argument("service_name", help="삭제할 서비스명")

    # list
    sub.add_parser("list", help="서비스 목록")

    # init
    sub.add_parser("init", help="초기 설정 (기존 구성 마이그레이션)")

    args = parser.parse_args()
    handlers = {
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "init": cmd_init,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
