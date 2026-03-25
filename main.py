import os
import subprocess
import re
from pathlib import Path
import shutil
import anthropic
from discord_webhook import DiscordWebhook

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-opus-4-5')
TITLE_KEYWORDS = os.getenv('TITLE_KEYWORDS', 'Stock Market Today')
CHANNEL_URL = 'https://www.youtube.com/@investorsbusinessdaily/videos'

def get_latest_video_url():
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--match-title', TITLE_KEYWORDS,
        '--dateafter', 'today',
        '--print', 'url',
        CHANNEL_URL
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to get video URL: {result.stderr}")
    urls = result.stdout.strip().split('\n')
    if not urls or urls[0] == '':
        raise Exception("No video found matching criteria")
    return urls[0]

def download_subs(video_url):
    cmd = [
        'yt-dlp',
        '--write-auto-sub',
        '--sub-lang', 'en',
        '--skip-download',
        '-o', 'temp',
        video_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to download subs: {result.stderr}")
    sub_file = Path('temp.en.vtt')
    if sub_file.exists():
        return str(sub_file)
    raise Exception("Sub file not found")

def parse_vtt(vtt_path):
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    text_lines = []
    for line in lines:
        if '-->' not in line and line.strip() and not line.startswith('WEBVTT'):
            text_lines.append(line.strip())
    transcript = ' '.join(text_lines)
    transcript = re.sub(r'\s+', ' ', transcript)
    return transcript

def summarize_transcript(transcript):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Summarize this IBD Stock Market Today transcript, focusing on:

- Current market status and key levels
- Distribution days and accumulation days
- Sector rotation and leadership
- Specific tickers mentioned with price levels
- Actionable takeaways for traders

Transcript:

{transcript}

"""
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def send_to_discord(message):
    # Discord has 2000 char limit, split if needed
    if len(message) <= 2000:
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=message)
        response = webhook.execute()
        if response.status_code != 200:
            raise Exception(f"Failed to send to Discord: {response.status_code}")
    else:
        parts = [message[i:i+2000] for i in range(0, len(message), 2000)]
        for part in parts:
            webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=part)
            response = webhook.execute()
            if response.status_code != 200:
                raise Exception(f"Failed to send to Discord: {response.status_code}")

def main():
    try:
        video_url = get_latest_video_url()
        print(f"Found video: {video_url}")
        sub_path = download_subs(video_url)
        transcript = parse_vtt(sub_path)
        summary = summarize_transcript(transcript)
        print("\n===== SUMMARY =====")
        print(summary)
        print("===================\n")
        with open('last_summary.txt', 'w', encoding='utf-8') as f:
            f.write(summary)
        send_to_discord(f"**IBD Stock Market Today Summary**\n\n{summary}")
        print("Summary sent to Discord")
        # Clean up
        if Path('temp.en.vtt').exists():
            Path('temp.en.vtt').unlink()
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        if DISCORD_WEBHOOK_URL:
            try:
                send_to_discord(f"**IBD Summarizer Error**\n\n{error_msg}")
            except:
                pass  # Avoid infinite loop

if __name__ == '__main__':
    main()