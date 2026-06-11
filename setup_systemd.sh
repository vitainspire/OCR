#!/bin/bash
# ─────────────────────────────────────────────────────────────
# setup_systemd.sh — Registers Door 1 and Door 2 as Services
# ─────────────────────────────────────────────────────────────

echo "Creating systemd service file for Door 1 (OCR)..."
sudo bash -c "cat > /etc/systemd/system/vllm-ocr.service" << 'EOF'
[Unit]
Description=vLLM Door 1 (OCR Fortress)
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/testing
ExecStart=/bin/bash /home/ec2-user/testing/start_server.sh ocr
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=vllm-ocr

[Install]
WantedBy=multi-user.target
EOF

echo "Creating systemd service file for Door 2 (Lightning Text)..."
sudo bash -c "cat > /etc/systemd/system/vllm-text.service" << 'EOF'
[Unit]
Description=vLLM Door 2 (Lightning Text)
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/testing
ExecStart=/bin/bash /home/ec2-user/testing/start_server.sh text
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=vllm-text

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Disabling old single-door service..."
sudo systemctl disable vllm.service || true
sudo systemctl stop vllm.service || true

echo "Enabling Door 1 and Door 2 to start on boot..."
sudo systemctl enable vllm-ocr.service
sudo systemctl enable vllm-text.service

echo "Starting Door 1 and Door 2 now..."
sudo systemctl start vllm-ocr.service
sudo systemctl start vllm-text.service

echo "Done! The Two-Door Architecture is fully deployed."
echo "Check Door 1 logs: sudo journalctl -u vllm-ocr -f"
echo "Check Door 2 logs: sudo journalctl -u vllm-text -f"
