#!/usr/bin/env python

import os
import sys
import subprocess

REQUIRED_PACKAGES = ["snscrape", "requests"]

def ensure_dependencies():
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            print(f"📦 Installing missing package: {pkg}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def run_thread_command(args):
    import re
    from urllib.parse import urlparse
    from datetime import datetime
    import snscrape.modules.twitter as sntwitter
    import requests

    if args.format != "markdown":
        print("❌ Only 'markdown' format is supported.")
        sys.exit(1)

    tweet_id = args.url.strip("/").split("/")[-1]
    os.makedirs(args.assets_path, exist_ok=True)

    def get_thread_upward(tweet_id):
        tweet = None
        for t in sntwitter.TwitterTweetScraper(tweet_id).get_items():
            tweet = t
            break
        if not tweet or not tweet.inReplyToTweetId:
            return [tweet] if tweet else []

        chain = [tweet]
        while tweet.inReplyToTweetId:
            prev_id = tweet.inReplyToTweetId
            for t in sntwitter.TwitterTweetScraper(prev_id).get_items():
                tweet = t
                chain.append(tweet)
                break
            else:
                break
        return list(reversed(chain))

    def sanitize_filename(text):
        return re.sub(r"[^a-zA-Z0-9_-]", "_", text)

    def download_image(url, tweet_id, index):
        ext = os.path.splitext(urlparse(url).path)[-1]
        filename = f"{tweet_id}_img{index}{ext}"
        path = os.path.join(args.assets_path, filename)
        if not os.path.exists(path):
            r = requests.get(url)
            with open(path, "wb") as f:
                f.write(r.content)
        return os.path.relpath(path, os.path.dirname(args.file_path))

    def tweet_to_md(tweet):
        dt = tweet.date.strftime("%Y-%m-%d %H:%M")
        md = f"## {dt}\n"
        md += tweet.content.strip() + "\n\n"
        for i, media in enumerate(tweet.media or []):
            if hasattr(media, "fullUrl"):
                image_path = download_image(media.fullUrl, tweet.id, i)
                md += f"![image{i}]({image_path})\n\n"
        md += "---\n\n"
        return md

    print(f"🔍 Fetching thread upward from tweet {tweet_id}...")
    thread = get_thread_upward(tweet_id)
    if not thread:
        print("❌ No thread found or invalid tweet ID.")
        sys.exit(1)

    print(f"✅ Retrieved {len(thread)} tweets from @{'unknown' if not thread[0] else thread[0].user.username}")

    os.makedirs(os.path.dirname(args.file_path), exist_ok=True)
    output_md = "# Thread by @" + thread[0].user.username + "\n\n"
    for t in thread:
        output_md += tweet_to_md(t)

    with open(args.file_path, "w", encoding="utf-8") as f:
        f.write(output_md)

    print(f"📄 Markdown saved to: {args.file_path}")

def main():
    ensure_dependencies()

    import argparse
    parser = argparse.ArgumentParser(prog="twitter-dl.py", description="Download Twitter content")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # thread subcommand
    thread_parser = subparsers.add_parser("thread", help="Download a Twitter thread upward from a tweet")
    thread_parser.add_argument("url", help="URL of the tweet to start from")
    thread_parser.add_argument("--format", choices=["markdown"], default="markdown", help="Output format")
    thread_parser.add_argument("--file-path", default="output/thread.md", help="Path to the output file")
    thread_parser.add_argument("--assets-path", default="output/images", help="Path to save images")
    thread_parser.set_defaults(func=run_thread_command)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
