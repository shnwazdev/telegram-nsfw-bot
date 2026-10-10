@echo off
title Telegram NSFW Auto-Delete Shield Bot 24/7
color 0b
echo ===============================================================
echo   Telegram NSFW Auto-Delete Shield Bot (Telethon MTProto)
echo   High-Speed In-Process AI Moderation (Zero Delay)
echo ===============================================================
:loop
python main.py
echo [!] Bot process terminated. Auto-restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
