# 🚀 Deploying the Telegram Bot

The static API is already "hosted" via jsDelivr (it just works™).
The **Telegram bot** is the piece that needs a long-running server.

## Option 1: Coolify on Your Existing VPS (Recommended)

You already have Coolify running, so this is the simplest path.

### Coolify Steps

1. **Push the repo** (already pushed to `github.com/jack-kitto/based-dev-quotes`).

2. **In Coolify**: Create → Resource → **Private Repository**, point to your GitHub repo.

3. **Build Pack**: Docker Compose (it'll auto-detect `.coolify.yml`).

4. **Set Environment Variables** in Coolify's Secrets tab:
   - `TELEGRAM_BOT_TOKEN` = your bot token (e.g., `8009828977:AAF...`)
   - `GITHUB_TOKEN` = your GitHub PAT (needs `repo` scope)
   - `OPENROUTER_API_KEY` = your OpenRouter key (only needed if you want auto-submissions)
   - `QUOTE_MODEL` = optional, defaults to `google/gemini-2.5-flash`

5. **Persistent Storage**: Make sure the `/app/quotes` and `/app/api` volumes persist across deployments (Coolify handles this automatically with named volumes, but verify in the volume config).

6. **Deploy**: Hit the Deploy button. Bot should start polling within 30 seconds.

### Coolify Health Check

The Docker setup includes a healthcheck. In Coolify, enable "Health Check" on the service so it auto-restarts if the bot crashes.

### Custom Domain (Optional)

You can route through Cloudflare → Coolify → this service. But really, the bot doesn't need to be publicly reachable — it just needs outbound HTTPS to Telegram's API.

---

## Option 2: Plain systemd Service on VPS

If you don't want to bother with Docker:

```bash
# On your VPS
git clone https://github.com/jack-kitto/based-dev-quotes.git /opt/based-dev-quotes
cd /opt/based-dev-quotes

# Create the systemd service
cat > /etc/systemd/system/based-quotes-bot.service << 'EOF'
[Unit]
Description=based-dev-quotes Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/based-dev-quotes
ExecStart=/usr/bin/python3 /opt/based-dev-quotes/scripts/telegram_bot.py
Restart=always
RestartSec=10
EnvironmentFile=/opt/based-dev-quotes/.env

[Install]
WantedBy=multi-user.target
EOF

# Add credentials
cat > /opt/based-dev-quotes/.env << 'EOF'
TELEGRAM_BOT_TOKEN=your-token-here
GITHUB_TOKEN=your-gh-token-here
OPENROUTER_API_KEY=your-openrouter-key
EOF
chmod 600 /opt/based-dev-quotes/.env

# Enable & start
systemctl daemon-reload
systemctl enable based-quotes-bot
systemctl start based-quotes-bot

# Check
systemctl status based-quotes-bot
journalctl -u based-quotes-bot -f
```

---

## Option 3: Fly.io (Free Tier)

```bash
# Install fly CLI
curl -L https://fly.io/install.sh | sh

# In the repo
fly launch --name based-quotes-bot --copy-config
# Select "no postgres" or similar
# Edit the generated Dockerfile path to ./Dockerfile

# Set secrets
fly secrets set TELEGRAM_BOT_TOKEN="..."
fly secrets set GITHUB_TOKEN="..."

# Deploy
fly deploy
```

---

## Bot Behavior

Once running:
- `/submit <quote> — <author>` queues to `quotes/submissions.json`
- `/random`, `/today`, `/stats` work immediately from the bundled dataset
- Run `python3 scripts/process_submissions.py` (manually or via cron) to flush submissions → opens a PR for review

## Processing Submissions Automatically

Add a cron job (e.g., on the VPS) that runs daily:

```bash
# /etc/cron.d/based-quotes-process
0 9 * * * root cd /opt/based-dev-quotes && python3 scripts/process_submissions.py >> /var/log/based-quotes.log 2>&1
```

Or, to make it fancier, set it up as a second Coolify service that runs a one-shot job daily.

---

## Security Notes

- **Never commit `TELEGRAM_BOT_TOKEN` or `GITHUB_TOKEN` to git.** Always use env vars.
- The `Dockerfile` and `.coolify.yml` use `${VARIABLE}` references — Coolify injects the actual values from its secrets store at runtime.
- Regenerate your Telegram token if it ever leaks.
