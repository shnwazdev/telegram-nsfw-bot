#!/usr/bin/env bash
set -e

echo "🚀 Starting Telegram NSFW Shield Bot..."
python3 -m pip install -r requirements.txt
python3 main.py
