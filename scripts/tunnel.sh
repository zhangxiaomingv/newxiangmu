#!/bin/bash
TUNNEL_LOG="/home/zxm/zkoner/data/tunnel.log"
echo "[$(date)] Starting tunnel..." >> "$TUNNEL_LOG"
pkill -f "localtunnel" 2>/dev/null
sleep 1
cd /home/zxm/zkoner/backend
npx localtunnel --port 8000 >> "$TUNNEL_LOG" 2>&1
