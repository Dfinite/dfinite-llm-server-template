#!/usr/bin/env python3
"""
Config → .env 변환기
configs/*.yaml을 읽어 docker-compose용 .env 파일을 생성합니다.
chat, reranker, embedding 모든 타입을 지원합니다.
"""

import sys
import yaml
from pathlib import Path


def parse_config(config_path: str) -> dict:
    """YAML 설정을 읽어 docker-compose .env 변수로 변환"""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    model = cfg.get("model", {})
    vllm = cfg.get("vllm", {})
    env_vars = vllm.get("env", {})
    extra_args = vllm.get("extra_args", [])

    # ── vLLM serve 명령어 인자 조립 ──
    # 내부 포트는 8000 고정 (vLLM 기본값), config의 port는 호스트 포트로 사용
    # v0.18.0+: model은 positional argument로 전달
    cmd_parts = [
        model["path"],
        "--host", "0.0.0.0",
        "--port", "8000",
    ]

    # runner 모드 (reranker/embedding용)
    runner = vllm.get("runner")
    if runner:
        cmd_parts.extend(["--runner", str(runner)])

    # task (reranker: score, embedding: embed)
    task = vllm.get("task")
    if task:
        cmd_parts.extend(["--task", str(task)])

    # 핵심 파라미터
    param_map = {
        "tensor_parallel_size": "--tensor-parallel-size",
        "max_model_len": "--max-model-len",
        "gpu_memory_utilization": "--gpu-memory-utilization",
        "dtype": "--dtype",
        "reasoning_parser": "--reasoning-parser",
        "tool_call_parser": "--tool-call-parser",
        "quantization": "--quantization",
        "logits_processor_pattern": "--logits-processor-pattern",
    }

    for yaml_key, cli_flag in param_map.items():
        val = vllm.get(yaml_key)
        if val is not None and str(val).lower() not in ("none", "null", ""):
            cmd_parts.extend([cli_flag, str(val)])

    # bool 플래그
    bool_flags = {
        "trust_remote_code": "--trust-remote-code",
        "enforce_eager": "--enforce-eager",
        "enable_prefix_caching": "--enable-prefix-caching",
        "enable_auto_tool_choice": "--enable-auto-tool-choice",
    }

    for yaml_key, cli_flag in bool_flags.items():
        val = vllm.get(yaml_key)
        if val is True:
            cmd_parts.append(cli_flag)

    # extra_args 추가
    if extra_args:
        cmd_parts.extend(str(a) for a in extra_args)

    # ── .env 변수 생성 ──
    env = {
        "MODEL_NAME": model.get("name", "default"),
        "MODEL_PATH": model["path"],
        "HOST_PORT": str(vllm.get("port", 8000)),
        "VLLM_CMD_ARGS": " ".join(cmd_parts),
    }

    # 환경변수 전달
    for k, v in env_vars.items():
        env[k] = str(v)

    return env


def write_env(env: dict, output_path: str = ".env"):
    """딕셔너리를 .env 파일로 저장"""
    lines = []
    for k, v in env.items():
        # 공백 포함 시 따옴표로 감싸기
        if " " in v or '"' in v:
            v_escaped = v.replace('"', '\\"')
            lines.append(f'{k}="{v_escaped}"')
        else:
            lines.append(f"{k}={v}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_config.py <config.yaml> [output.env]")
        sys.exit(1)

    config_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else ".env"

    if not Path(config_path).exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    env = parse_config(config_path)
    write_env(env, output_path)

    # 디버그 출력
    print(f"Model:   {env['MODEL_NAME']}")
    print(f"Port:    {env['HOST_PORT']}")
    print(f"Command: vllm serve {env['VLLM_CMD_ARGS']}")
    print(f"Env:     {output_path}")


if __name__ == "__main__":
    main()
