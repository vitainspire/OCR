# 🚀 The "Two-Door" Educational AI API
### Enterprise-Grade Parallel LLM & VLM Architecture

This repository contains the complete infrastructure, crash-proof testing suite, and one-command deployment for an educational AI routing system. It uses a **Two-Door Architecture** that serves OCR vision requests and text-generation (lesson-plan) requests in parallel on a single GPU using vLLM continuous batching.

---

## 🏗️ Architecture Overview

Both engines run on a single NVIDIA L4 (24 GB) instance, on different ports, as independent OpenAI-compatible API endpoints. **Both run on the same modern vLLM 0.22 environment** (`vllm_ocr_env`).

* **🚪 Door 1 (OCR Vision Engine) — Port 8000**
  * **Model:** `Qwen/Qwen2.5-VL-7B-Instruct-AWQ` (served as `ocr-engine`)
  * **Role:** 7B Vision-Language model for handwriting / printed-text OCR.
  * **GPU:** `--gpu-memory-utilization 0.40` (~6.7 GB)

* **🚪 Door 2 (Creative Text Engine) — Port 8001**
  * **Model:** `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` (served as `text-engine`)
  * **Role:** Fast text generator for creative lesson plans.
  * **GPU:** `--gpu-memory-utilization 0.40` (~5.4 GB)

> ⚠️ **Important:** the OCR model (Qwen2.5-VL) is **only** supported by vLLM ≥ 0.7. The old vLLM 0.6.1 cannot load it and also 500s on text generation (missing `pyairports`). `setup_aws.sh` installs **vLLM 0.22.1** for both doors — do not downgrade.

---

## ✅ Prerequisites — AWS Console (one-time per new instance)

These are AWS launch settings; they are **not** part of the repo, so set them when you create the instance:

| Setting | Value |
|---|---|
| **AMI** | `ami-052db9c269f0d6a4c` — Amazon Linux 2023 **NVIDIA GPU** AMI *(region `eu-north-1`; AMI IDs are region-specific)* |
| **Instance type** | `g6.2xlarge` (1× NVIDIA L4, 24 GB VRAM, 8 vCPU) |
| **Root volume** | **80 GB** gp3 (the default 50 GB is too small — model download fails with "No space left on device") |
| **Security group** | Allow inbound **TCP 22** (SSH), **8000**, and **8001** |
| **Elastic IP** | Associate one (e.g. `13.62.96.5`) so the address is stable across restarts |

---

## 💻 Setup — make the pipeline live (3 commands)

> 🖥️ **Which terminal?** These commands run **on the server**, inside an SSH session.
> - First connect from your **laptop**: `ssh -i "path\to\written.pem" ec2-user@<ELASTIC_IP>`
> - Wait until the prompt changes to `[ec2-user@ip-...]$` — that means you're **on the server**.
> - Only then run the commands below. (If you see `PS C:\...>` you're still on your laptop — `bash`/`cd ~/testing` will fail there.)

```bash
git clone https://github.com/vitainspire/OCR.git ~/testing
cd ~/testing
bash setup_aws.sh
```

`setup_aws.sh` does **everything automatically**:
1. Installs `python3.11`, `python3.11-devel`, `python3.11-pip`, `gcc` (devel headers + gcc are required — vLLM/Triton JIT-compiles a CUDA helper at startup and crashes without them).
2. Creates the `vllm_ocr_env` virtual environment and installs **vLLM 0.22.1**.
3. Registers both doors as **systemd services** (`vllm-ocr`, `vllm-text`), enabled to auto-start on boot and auto-restart on crash.
4. Starts both services and downloads the models (~12 GB total).

⏱️ First run takes **~10–15 minutes** (mostly the model download). When you see this, the server is **live**:
```
BOTH DOORS FULLY OPERATIONAL!
```

---

## 🔎 Verify it's running (on the server)

```bash
systemctl status vllm-ocr vllm-text     # both should be "active (running)"
curl -s http://localhost:8000/v1/models  # -> ocr-engine
curl -s http://localhost:8001/v1/models  # -> text-engine
```

Quick functional test (no images needed) — Door 2:
```bash
curl -s http://localhost:8001/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"text-engine","messages":[{"role":"user","content":"One creative hook to teach gravity."}],"max_tokens":80}'
```

---

## 🧪 Full benchmark — run from your LAPTOP (not the server)

`benchmark_parallel.py` reads images from a **local** folder (`IMAGE_DIR`) and hits the server's public IP, so it runs on your laptop in a **local** PowerShell (`PS C:\...>`), not the SSH terminal.

1. Put test images in the folder set by `IMAGE_DIR` in `benchmark_parallel.py`.
2. Set `SERVER_IP` to your instance's Elastic IP.
3. Run:
   ```powershell
   cd D:\testing
   python benchmark_parallel.py
   ```
Results are stored in `tasks.db`. Completed tasks are skipped on re-runs; to force a fresh run:
```powershell
python -c "import sqlite3;c=sqlite3.connect('tasks.db');c.execute(\"UPDATE jobs SET status='PENDING'\");c.commit()"
```

---

## 🛠️ Day-2 operations (on the server)

```bash
sudo systemctl restart vllm-ocr vllm-text   # restart both doors
sudo systemctl stop    vllm-ocr vllm-text   # stop both
sudo journalctl -u vllm-ocr  -f             # live OCR logs
sudo journalctl -u vllm-text -f             # live text logs
```

To change settings (model, ports, concurrency), edit `~/testing/start_server.sh` then `sudo systemctl restart vllm-ocr vllm-text`. For example, raise OCR throughput by increasing `--max-num-seqs 4` to `8`.

---

## 🩺 Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `bash: python: command not found` on the server | Use `python3`, or `source ~/vllm_ocr_env/bin/activate` first. `python` only exists inside the venv. |
| `cd: D:\testing: No such file` / `bash: not recognized` | You're running **laptop** commands in the **server** SSH terminal (or vice-versa). Check the prompt. |
| Download fails: `No space left on device` | Root volume too small — launch with **80 GB+**. |
| Engine crash-loops: `gcc ... cuda_utils.c ... non-zero exit` | Missing `python3.11-devel` (Python.h). `setup_aws.sh` installs it; re-run if you skipped it. |
| OCR door: `Qwen2_5_VLForConditionalGeneration not supported` | vLLM too old. Must be 0.22.x (handled by `setup_aws.sh`). |
| Benchmark: `Cannot connect to host ...:8000` | Security group isn't allowing inbound 8000/8001. |

---

## ⚡ Faster rebuilds (optional)

Instead of re-running `setup_aws.sh` (re-downloads 12 GB), create an **AMI image** of a working instance from the AWS Console. New instances launched from that AMI boot with the venv, models, and services already baked in — the pipeline comes up automatically, no setup needed.
