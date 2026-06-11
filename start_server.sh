#!/bin/bash
# ─────────────────────────────────────────────────────────────
# start_server.sh  —  The Enterprise Two-Door Architecture
# ─────────────────────────────────────────────────────────────
# Usage:
#   bash ~/start_server.sh ocr   (Door 1 - Port 8000)
#   bash ~/start_server.sh text  (Door 2 - Port 8001)
# ─────────────────────────────────────────────────────────────

set -e

VENV="$HOME/vllm_env"

echo "==> Activating vllm_env..."
source "$VENV/bin/activate"

# Navigate to the script's directory (where the patches are located)
cd "$(dirname "$0")"

if [ "$1" == "ocr" ]; then
    echo "==> Applying monkey patches for Qwen2.5-VL compatability..."
    python3 patch_qwen.py || true
    python3 patch.py || true
    python3 patch2.py || true
    python3 patch3.py || true

    echo "==> Starting Door 1 (OCR Fortress) on Port 8000..."
    python -m vllm.entrypoints.openai.api_server \
        --model "Qwen/Qwen2.5-VL-7B-Instruct-AWQ" \
        --quantization awq \
        --dtype float16 \
        --enforce-eager \
        --gpu-memory-utilization 0.40 \
        --max-model-len 3072 \
        --max-num-seqs 4 \
        --enable-prefix-caching \
        --host 0.0.0.0 \
        --port 8000 \
        --served-model-name ocr-engine \
        --trust-remote-code

elif [ "$1" == "text" ]; then
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
