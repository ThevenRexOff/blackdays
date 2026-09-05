#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || true
exec .venv/bin/python telegram_bot.py
