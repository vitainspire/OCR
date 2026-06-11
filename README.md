# 🚀 The "Two-Door" Educational AI API
### Enterprise-Grade Parallel LLM & VLM Architecture

This repository contains the complete infrastructure, crash-proof testing suite, and deployment logic for an advanced educational AI routing system. It uses a **Two-Door Architecture** capable of processing 15+ simultaneous OCR vision requests and 60+ simultaneous text-generation requests in parallel using vLLM continuous batching.

---

## 🏗️ Architecture Overview

To maximize GPU utilization on a single 24GB VRAM instance, the system hosts two massive open-source models natively on exactly **different ports** acting as individual API endpoints:

* **🚪 Door 1 (OCR Vision Engine) — Port 8000**
  * **Model:** `Qwen/Qwen2.5-VL-7B-Instruct-AWQ`
  * **Role:** A 7-billion parameter Vision Language Model optimized for perfect handwriting and textbook OCR.
  * **VRAM Allocation:** ~40% (9.6 GB)

* **🚪 Door 2 (Creative Text Engine) — Port 8001**
  * **Model:** `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` (Speculatively decoding with `Llama-3.2-1B`)
  * **Role:** A blazing fast text generator specifically tuned with FP8 KV-Cache to batch generate highly creative lesson plans.
  * **VRAM Allocation:** ~45% (10.8 GB)

---

## 🛠️ Step 1: AWS Provisioning

To recreate this exact setup from scratch, you must rent the correct hardware:
1. Log into the AWS Console.
2. Launch a new EC2 Instance: **`g6.2xlarge`** (This provides 1x NVIDIA L4 GPU with 24GB VRAM and 8 vCPUs).
3. **AMI (Operating System):** Select **Ubuntu 22.04 LTS** (Deep Learning AMI recommended).
4. **Storage:** Allocate at least **150 GB gp3 SSD**.

---

## 💻 Step 2: Server Installation

SSH into your new AWS instance and run the following to install vLLM:

```bash
# Update OS and install python tools
sudo apt update
sudo apt install python3-venv python3-pip git -y

# Create a virtual environment
python3 -m venv vllm_env
source vllm_env/bin/activate

# Install vLLM and dependencies
pip install vllm
pip install qwen-vl-utils torchvision
```

**Upload the Code:** 
Transfer this GitHub repository to the `/home/ubuntu/` directory of your AWS server.

---

## 🩹 Step 3: Qwen2.5-VL Monkey Patches

Qwen2.5-VL has known compatibility bugs with standard vLLM chunked prefill. We have provided `patch.py`, `patch2.py`, `patch3.py`, and `patch_qwen.py`. 

**You do not need to run these manually.** They are automatically executed by the `start_server.sh` script every time the server boots.

---

## 🛡️ Step 4: Autonomous "Self-Healing" Deployment

To ensure you don't have to manually start the servers every time AWS boots, and to guarantee the models instantly restart if they crash (e.g., Out of Memory errors), we use Linux `systemd`.

Run these exact commands in your AWS terminal:

**Create Door 1 Service:**
```bash
sudo nano /etc/systemd/system/vllm-ocr.service
```
Paste this inside:
```ini
[Unit]
Description=vLLM OCR Engine (Door 1)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/bin/bash /home/ubuntu/start_server.sh ocr
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
*(Save and exit)*

**Create Door 2 Service:**
```bash
sudo nano /etc/systemd/system/vllm-text.service
```
Paste this inside:
```ini
[Unit]
Description=vLLM Text Engine (Door 2)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/bin/bash /home/ubuntu/start_server.sh text
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
*(Save and exit)*

**Enable and Start the Autonomous Engines:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable vllm-ocr.service
sudo systemctl enable vllm-text.service
sudo systemctl start vllm-ocr.service
sudo systemctl start vllm-text.service
```

*(You can check if they are running via `sudo systemctl status vllm-ocr.service`)*

---

## 🧪 Step 5: The Crash-Proof Parallel Benchmark

This repository includes a highly advanced benchmarking tool: `benchmark_parallel.py`.

It utilizes `asyncio` to simultaneously hit both Door 1 and Door 2. More importantly, it uses an internal **SQLite Database** (`tasks.db`) to ensure that if the connection to AWS drops, you do not lose your generated outputs.

**To test the server limits locally:**
1. Put test images in your local `IMAGE_DIR`.
2. Update the `SERVER_IP` inside `benchmark_parallel.py` to match your new AWS Public IP.
3. Run the benchmark:
```bash
python benchmark_parallel.py
```
If you interrupt the script and run it again, it will read the SQLite database, skip the completed tasks, and seamlessly resume from where it left off!
