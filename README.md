# IBD Stock Market Today — Daily Video Summarizer

Automatically finds today's IBD "Stock Market Today" YouTube video, extracts the transcript, summarizes it with Claude (structured for Minervini/O'Neil traders), and posts to Discord.

## Architecture

```
Railway Cron (Mon-Fri)
  → yt-dlp: find today's video on IBD channel
  → yt-dlp: extract YouTube auto-captions (.vtt)
  → Claude API: structured summary (market status, sectors, stocks, action items)
  → Discord webhook: deliver to your trading channel
```

## Railway Deployment

### 1. Create Discord Webhook

- In your Discord server → channel settings → Integrations → Webhooks
- Create webhook, copy the URL

### 2. Deploy to Railway

```bash
# Option A: Deploy from GitHub
# Push this folder to a GitHub repo, connect it in Railway

# Option B: Deploy with Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

### 3. Set Environment Variables

In Railway dashboard → your service → Variables:

| Variable             | Required | Description                                |
|----------------------|----------|--------------------------------------------|
| `DISCORD_WEBHOOK_URL`| ✅       | Discord webhook URL                        |
| `ANTHROPIC_API_KEY`  | ✅       | Your Anthropic API key                     |
| `CLAUDE_MODEL`       | ❌       | Default: `claude-3-5-sonnet-20241022`      |
| `LOOKBACK_HOURS`     | ❌       | How far back to search (default: 36)       |
| `TITLE_KEYWORDS`     | ❌       | Comma-free keyword match (default: "Stock Market Today") |
| `IBD_CHANNEL_URL`    | ❌       | Override channel URL                       |

### 4. Set Cron Schedule

In Railway dashboard → your service → Settings → Cron Schedule:

```
0 0 * * 1-5
```

This runs at **midnight UTC Mon-Fri** = 7pm ET = ~1pm NZDT next day.

Adjust based on when IBD typically publishes (usually 4-6pm ET):
- `0 23 * * 1-5` → 6pm ET (conservative, same day)
- `0 0 * * 1-5`  → 7pm ET (safe default)
- `0 4 * * 2-6`  → 11pm ET (if you want it waiting for your morning)

## Customization

### Add More Channels

Edit `TITLE_KEYWORDS` and `IBD_CHANNEL_URL` env vars, or duplicate the service for other channels. Works with any YouTube channel that posts regular content.

### Modify the Summary Format

Edit the `SUMMARY_PROMPT` in `main.py` to adjust sections, add/remove detail, or change the trading framework emphasis.

### Cost

- **yt-dlp + captions**: Free
- **Claude API**: ~$0.01-0.03 per summary (depending on transcript length)
- **Railway**: Cron job runs ~2 min/day, well within free/hobby tier
- **Total**: Roughly $1-2/month

## Local Testing

```bash
# Set env vars
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Install deps
pip install -r requirements.txt

# Ensure yt-dlp and ffmpeg are installed
# macOS: brew install yt-dlp ffmpeg
# Ubuntu: apt install ffmpeg && pip install yt-dlp

# Run
python main.py
```

## Troubleshooting

- **"No video found"**: IBD may not have published yet. Increase `LOOKBACK_HOURS` or adjust cron timing.
- **Transcript extraction fails**: Some videos have captions disabled. The script posts a notification to Discord so you know.
- **Discord rate limits**: Built-in retry logic handles this. If persistent, space out runs.