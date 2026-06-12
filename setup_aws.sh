#!/bin/bash
# ─────────────────────────────────────────────────────────────
# setup_aws.sh — Provision a fresh GPU instance for the
#                Two-Door Architecture (OCR + Text).
#
# Target : Amazon Linux 2023 NVIDIA GPU AMI (NVIDIA driver +
#          python3.11 preinstalled), instance type g6.2xlarge (L4).
# Run    : place repo at /home/ec2-user/testing, then:  bash setup_aws.sh
#
# IMPORTANT — launch the instance with an 80GB+ root EBS volume.
#   The two AWQ models (~7GB OCR + ~5.4GB text) plus the venv (~9GB)
#   do NOT fit on the default 50GB volume; downloads fail with
#   "No space left on device" (ENOSPC). On a fresh launch AL2023
#   cloud-init auto-grows the partition to the volume size, so just
#   pick 80GB+ at launch time.
# ─────────────────────────────────────────────────────────────
set -e
export HF_HUB_DISABLE_XET=1   # avoid hf_xet downloader crash on model pull

echo "==> Installing python3.11 + build deps (base AMI may ship only python3.9)..."
# python3.11-devel (Python.h) + gcc are REQUIRED: vLLM/Triton JIT-compiles a
# small CUDA helper at startup; without the dev headers it crashes with
# 'subprocess.CalledProcessError: gcc ... cuda_utils.c'.
sudo dnf install -y python3.11 python3.11-pip python3.11-devel gcc

echo "==> Creating vllm_ocr_env (vLLM 0.22 — supports Qwen2.5-VL AND Llama AWQ)..."
# Both doors run on this single modern env. Do NOT install vLLM 0.6.1:
# it cannot load Qwen2.5-VL and 500s on text gen (outlines/pyairports).
python3.11 -m venv ~/vllm_ocr_env
source ~/vllm_ocr_env/bin/activate
pip install --upgrade pip
pip install "vllm==0.22.1"

echo "==> Registering Door 1 (OCR) systemd service..."
cat << 'INNER_EOF' | sudo tee /etc/systemd/system/vllm-ocr.service
[Unit]
Description=vLLM OCR Engine (Door 1)
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/testing
ExecStart=/bin/bash /home/ec2-user/testing/start_server.sh ocr
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
INNER_EOF

echo "==> Registering Door 2 (Text) systemd service..."
cat << 'INNER_EOF' | sudo tee /etc/systemd/system/vllm-text.service
[Unit]
Description=vLLM Text Engine (Door 2)
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/testing
ExecStart=/bin/bash /home/ec2-user/testing/start_server.sh text
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
INNER_EOF

sudo systemctl daemon-reload
sudo systemctl enable vllm-ocr.service
sudo systemctl enable vllm-text.service

sudo systemctl start vllm-ocr.service
echo "Waiting for Door 1 to boot (first run downloads ~7GB, be patient)..."
for i in {1..180}; do
  if curl -s http://127.0.0.1:8000/v1/models >/dev/null; then echo "DOOR 1 READY"; break; fi
  sleep 5
done

sudo systemctl start vllm-text.service
echo "Waiting for Door 2 to boot (first run downloads ~5.4GB)..."
for i in {1..180}; do
  if curl -s http://127.0.0.1:8001/v1/models >/dev/null; then echo "DOOR 2 READY"; break; fi
  sleep 5
done

echo "BOTH DOORS FULLY OPERATIONAL!"
echo "  OCR : http://0.0.0.0:8000/v1  (model: ocr-engine)"
echo "  Text: http://0.0.0.0:8001/v1  (model: text-engine)"
echo "Logs: sudo journalctl -u vllm-ocr -f   |   sudo journalctl -u vllm-text -f"
