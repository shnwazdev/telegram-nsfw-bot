# 🛡️ Telegram NSFW Auto-Delete Shield Bot

An ultra-high-speed, 24/7 autonomous Telegram moderation bot powered by **Telethon MTProto** and an in-process **Hybrid AI ONNX Engine** (Yahoo OpenNSFW ResNet + NudeNet YOLO).

Engineered to detect and auto-delete 18+ stickers, porn media, explicit line-art, erotic poses, and edited messages in **< 40ms**.

---

## ✨ Features

- ⚡ **Zero-Network In-Process AI Evaluation**: Telethon MTProto downloads previews directly into memory and passes them to local ONNX models with **zero HTTP latency**.
- 🔞 **18+ Sticker & Media Auto-Deletion**:
  - WebP stickers, animated stickers, video stickers, photos, and GIFs.
  - Detects exposed genitalia, female breasts, buttocks, and anus.
  - CLAHE contrast enhancement detects Black & White erotic stickers and explicit line-art.
  - Sex positions & adult pose detection.
  - Works for all regular group members and administrators.
- 🛑 **Edit Guardian**:
  - Automatically deletes edited messages and edited medias in groups to prevent scams and copyright infringement.
- 🎛️ **Per-Group Feature Controls**:
  - `/nsfw on` / `/nsfw off` — Toggle NSFW sticker & media deletion.
  - `/edit on` / `/edit off` — Toggle Edit Guardian.
  - `/settings` — Interactive inline panel with toggle buttons.
- 🚪 **Auto-Leave on Admin Rights Revocation**:
  - If the bot is demoted or removed from administrators in any group, it alerts the group, automatically leaves, and logs the incident.
- 📝 **Live Audit Logging Channel (`-1003951821704`)**:
  - Logs when a user starts the bot (mention, user ID, username).
  - Logs when the bot is added to a group (group title, group ID, member count, added-by mention).
  - Logs when the bot auto-leaves due to demotion.
- 📢 **Owner Broadcast System (`Owner ID: 8677818347`)**:
  - `/broadcast <message>` or reply to any photo/sticker/post with `/broadcast`.
  - Reaches 100% of registered users and groups stored in SQLite database.
- 🖼️ **Spoiler Welcome Card**:
  - Sends interactive welcome banner formatted with native Telegram spoiler blur and clean blockquote explanations.

---

## 📁 Repository Structure

```
telegram-nsfw-bot/
├── src/
│   ├── __init__.py
│   ├── bot.py             # Telethon MTProto client, handlers, and moderation loops
│   ├── engine.py          # Dual ONNX AI inference engine (OpenNSFW + NudeNet)
│   ├── database.py        # SQLite persistent storage (users, groups, toggles)
│   └── config.py          # Environment settings & thresholds
├── models/
│   └── open_nsfw.onnx     # Fast ONNX classification model
├── assets/
│   └── banner.jpg         # Spoiler welcome banner image
├── Dockerfile             # Multi-cloud container definition
├── docker-compose.yml     # Compose with restart: always
├── Procfile               # Worker config for Heroku / Railway / Render / Koyeb
├── render.yaml            # Render Blueprint 1-click deploy
├── railway.toml           # Railway deploy configuration
├── requirements.txt       # Production dependencies
├── .env.example           # Configuration template
├── run.bat                # Windows 24/7 supervisor runner
├── start.sh               # Linux VPS runner script
├── telegram_nsfw_bot.service # Linux systemd service for 24/7 background run
└── main.py                # Bot entrypoint
```

---

## 🚀 How to Host Everywhere

### 1. ☁️ Host on Render (Free Background Worker)
1. Fork or push this repository to your GitHub account.
2. Sign in to [Render](https://render.com).
3. Click **New +** → **Blueprint** and connect your repository.
4. Render will read `render.yaml` automatically and configure the worker.
5. Set the required Environment Variables:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_BOT_TOKEN`
   - `OWNER_ID`
   - `LOG_GROUP_ID`
6. Click **Deploy**!

---

### 2. 🚆 Host on Railway
1. Sign in to [Railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select this repository.
4. Add the environment variables from `.env.example`.
5. Railway will automatically build via `railway.toml` / `Procfile` and keep the bot running 24/7!

---

### 3. 🐳 Host with Docker & Docker Compose
```bash
# Clone the repository
git clone https://github.com/shnwazdev/telegram-nsfw-bot.git
cd telegram-nsfw-bot

# Copy .env.example to .env and insert your bot token
cp .env.example .env

# Run in background with auto-restart enabled
docker compose up -d --build
```

---

### 4. 🐧 Host on Linux VPS (Ubuntu / Debian / Oracle / AWS / Hetzner)

#### Quick Run:
```bash
git clone https://github.com/shnwazdev/telegram-nsfw-bot.git
cd telegram-nsfw-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

#### Run 24/7 as Systemd Service (Auto-Start on Boot):
```bash
# Copy service file
sudo cp telegram_nsfw_bot.service /etc/systemd/system/telegram_nsfw_bot.service

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable telegram_nsfw_bot
sudo systemctl start telegram_nsfw_bot

# Check logs
sudo journalctl -u telegram_nsfw_bot -f
```

---

### 5. 🪟 Host on Windows (Local / VPS)
1. Ensure Python 3.10+ is installed.
2. Double-click **`run.bat`**.
3. The supervisor loop will keep the bot running 24/7 and automatically restart it if your network interrupts.

---

## 🛠️ Bot Commands

| Command | Permission | Description |
| :--- | :--- | :--- |
| `/start` | Everyone | Interactive welcome card with spoiler banner |
| `/check` | Everyone | Reply to any photo/sticker to test AI verdict |
| `/settings` | Admins | Interactive panel to toggle NSFW shield and sensitivity |
| `/nsfw on` / `/nsfw off` | Admins | Toggle 18+ porn stickers & media deletion |
| `/edit on` / `/edit off` | Admins | Toggle Edit Guardian (edited message deletion) |
| `/stats` | Everyone | View registered users, active groups, and scan latency |
| `/broadcast <msg>` | Owner (`8677818347`) | Broadcast text or replied media to all users & groups |

---

## 📄 License
MIT License. Open-source and free for all communities.
