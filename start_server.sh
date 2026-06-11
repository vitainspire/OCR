#!/bin/bash
# ─────────────────────────────────────────────────────────────
# start_server.sh — The Enterprise Two-Door Architecture
#   Door 1 (OCR  / Qwen2.5-VL-7B-AWQ)  -> port 8000  (model: ocr-engine)
#   Door 2 (Text / Llama-3.1-8B-AWQ)   -> port 8001  (model: text-engine)
#
# Both doors run on vllm_ocr_env (vLLM 0.22.x), which natively supports
# Qwen2.5-VL. NOTE: the old vllm_env / vLLM 0.6.1 must NOT be used here —
# it cannot load Qwen2.5-VL (unsupported architecture) and 500s on text
# generation (outlines -> missing pyairports). Keep both doors on 0.22.
#
# Usage:
#   bash start_server.sh ocr    (Door 1 - Port 8000)
#   bash start_server.sh text   (Door 2 - Port 8001)
# ─────────────────────────────────────────────────────────────
set -e
export HF_HUB_DISABLE_XET=1   # avoid hf_xet downloader crash on model pull
cd "$(dirname "$0")"

VENV="$HOME/vllm_ocr_env"

if [ "$1" == "ocr" ]; then
    echo "==> Activating $VENV (vLLM 0.22 - native Qwen2.5-VL support)..."
    source "$VENV/bin/activate"

    echo "==> Starting Door 1 (OCR Fortress) on Port 8000..."
    python -m vllm.entrypoints.openai.api_server \
        --model "Qwen/Qwen2.5-VL-7B-Instruct-AWQ" \
        --quantization awq \
        --dtype float16 \
        --enforce-eager \
        --gpu-memory-utilization 0.40 \
        --max-model-len 3072 \
        --max-num-seqs 4 \
        --host 0.0.0.0 \
        --port 8000 \
        --served-model-name ocr-engine \
        --trust-remote-code

elif [ "$1" == "text" ]; then
    echo "==> Activating $VENV..."
    source "$VENV/bin/activate"

    echo "==> Starting Door 2 (Lightning Text) on Port 8001..."
    python -m vllm.entrypoints.openai.api_server \
        --model "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4" \
        --quantization awq \
        --dtype float16 \
        --enforce-eager \
        --gpu-memory-utilization 0.40 \
        --max-model-len 8192 \
        --host 0.0.0.0 \
        --port 8001 \
        --served-model-name text-engine \
        --trust-remote-code
else
    echo "Usage: bash start_server.sh [ocr|text]"
    exit 1
fi
