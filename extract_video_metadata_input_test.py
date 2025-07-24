import json
import subprocess
import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# Enhanced configuration
output_dir = "video_output"
os.makedirs(output_dir, exist_ok=True)

# Improved headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

def get_video_download_command(url):
    """Return customized yt-dlp command based on website"""
    if "mako.co.il" in url:
        return [
            "yt-dlp",
            "--cookies-from-browser", "chrome",
            "--write-info-json",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "--output", f"{output_dir}/%(title)s.%(ext)s",
            url
        ]
    elif "foxsports.com" in url:
        return [
            "yt-dlp",
            "--referer", "https://www.foxsports.com/",
            "--write-info-json",
            "--output", f"{output_dir}/%(title)s.%(ext)s",
            url
        ]
    else:  # Default command for other sites
        return [
            "yt-dlp",
            "--write-info-json",
            "--write-description",
            "--write-thumbnail",
            "--all-subs",
            "--convert-subs", "srt",
            "--output", f"{output_dir}/%(title)s.%(ext)s",
            url
        ]

def download_video(url):
    """Enhanced download function with better error handling"""
    try:
        cmd = get_video_download_command(url)
        print(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        # Print yt-dlp output for debugging
        print("yt-dlp output:")
        print(result.stdout)
        if result.stderr:
            print("yt-dlp errors:")
            print(result.stderr)
        
        # Find downloaded files
        for file in os.listdir(output_dir):
            if file.endswith((".mp4", ".webm", ".mkv", ".mov", ".flv")):
                video_file = os.path.join(output_dir, file)
                json_file = os.path.join(output_dir, os.path.splitext(file)[0] + ".info.json")
                return video_file, json_file
        
        return None, None
        
    except subprocess.TimeoutExpired:
        print("Download timed out after 2 minutes")
        return None, None
    except Exception as e:
        print(f"Download error: {str(e)}")
        return None, None

def main():
    print("Video Downloader - Enhanced Version")
    url = input("Enter video URL: ").strip()
    
    if not re.match(r'^https?://', url):
        print("Invalid URL format")
        return
    
    video_file, json_file = download_video(url)
    
    if video_file:
        print(f"\nSuccessfully downloaded:\n{video_file}")
        print(f"Metadata saved to:\n{json_file}")
    else:
        print("\nFailed to download video. Possible solutions:")
        print("1. Try with browser cookies:")
        print(f"   yt-dlp --cookies-from-browser chrome \"{url}\"")
        print("2. The video might be DRM-protected")
        print("3. Check if you need to be logged in")

if __name__ == "__main__":
    main()