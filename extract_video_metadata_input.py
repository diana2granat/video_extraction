import json
import subprocess
import os
import requests
from bs4 import BeautifulSoup
import re

# Configuration
output_dir = "video_output"
json_output_file = "video_metadata.json"
exif_output_file = "exif_output.txt"
exiftool_path = r"C:\Users\diana\Desktop\minute.ly\exiftool-13.32_64\exiftool.exe"

# Custom headers for Israeli sites
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.mako.co.il/"
}

def get_user_url():
    while True:
        url = input("Enter the webpage URL containing the video (e.g., https://example.com/page): ").strip()
        if re.match(r'^https?://[^\s/$.?#].[^\s]*$', url):
            return url
        print("Invalid URL. Please enter a valid URL starting with http:// or https://")

def handle_mako_video(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        video_id_match = re.search(r'videoID:\s*["\'](\d+)["\']', response.text)
        if not video_id_match:
            print("Could not find video ID in Mako page")
            return None, None
        
        video_id = video_id_match.group(1)
        print(f"Found Mako video ID: {video_id}")
        
        m3u8_url = f"https://keshethlslive-lh.akamaihd.net/i/{video_id}_@319237/index_700_av-p.m3u8"
        
        subprocess.run([
            "yt-dlp",
            "--no-check-certificate",
            "--ignore-errors",
            "--write-info-json",
            "--output", f"{output_dir}/%(title)s.%(ext)s",
            m3u8_url
        ], check=True)
        
        for file in os.listdir(output_dir):
            if file.endswith((".mp4", ".mkv", ".webm")):
                video_file = f"{output_dir}/{file}"
                json_file = f"{output_dir}/{os.path.splitext(file)[0]}.info.json"
                return video_file, json_file
        
        return None, None
        
    except Exception as e:
        print(f"Error handling Mako video: {e}")
        return None, None

def download_video(page_url):
    if "mako.co.il" in page_url:
        return handle_mako_video(page_url)
    
    try:
        subprocess.run([
            "yt-dlp",
            "--no-check-certificate",
            "--ignore-errors",
            "--write-info-json",
            "--write-description",
            "--write-thumbnail",
            "--all-subs",
            "--convert-subs", "srt",
            "--output", f"{output_dir}/%(title)s.%(ext)s",
            page_url
        ], check=True)
        
        for file in os.listdir(output_dir):
            if file.endswith((".mp4", ".webm", ".mkv", ".mov", ".flv")):
                video_file = f"{output_dir}/{file}"
                json_file = f"{output_dir}/{os.path.splitext(file)[0]}.info.json"
                return video_file, json_file
        
        return None, None
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e}")
        return None, None

def extract_exif_metadata(video_file):
    try:
        if os.path.exists(exif_output_file):
            os.remove(exif_output_file)
            
        result = subprocess.run(
            [exiftool_path, "-a", "-G", video_file],
            capture_output=True,
            text=True,
            check=True
        )
        
        with open(exif_output_file, "w") as f:
            f.write(result.stdout)
            
        exif_data = {}
        for line in result.stdout.splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                exif_data[key.strip()] = value.strip()
        return exif_data
    except subprocess.CalledProcessError as e:
        print(f"Error extracting ExifTool metadata: {e}")
        return {}

def compile_metadata(yt_json_file, exif_data):
    metadata = {
        "source_url": "N/A",
        "title": "N/A",
        "description": "N/A",
        "publication_date": "N/A",
        "categories_tags": ["N/A"],
        "duration": "N/A",
        "author_uploader": "N/A",
        "view_count": "N/A",
        "resolution": "N/A",
        "file_format": "N/A",
        "codecs": "N/A",
        "file_size": "N/A",
        "frame_rate": "N/A",
        "bit_rate": "N/A",
        "thumbnail": "N/A",
        "subtitles": "N/A"
    }

    if yt_json_file and os.path.exists(yt_json_file):
        with open(yt_json_file, "r") as f:
            try:
                yt_data = json.load(f)
                metadata.update({
                    "source_url": yt_data.get("webpage_url", "N/A"),
                    "title": yt_data.get("title", "N/A"),
                    "description": yt_data.get("description", "N/A"),
                    "publication_date": yt_data.get("upload_date", "N/A"),
                    "categories_tags": yt_data.get("tags", ["N/A"]),
                    "duration": yt_data.get("duration_string", str(yt_data.get("duration", "N/A"))),
                    "author_uploader": yt_data.get("uploader", "N/A"),
                    "view_count": str(yt_data.get("view_count", "N/A")),
                    "thumbnail": yt_data.get("thumbnail", "N/A")
                })
                
                if os.path.exists(yt_json_file.replace(".info.json", ".en.srt")):
                    metadata["subtitles"] = "Available"
            except json.JSONDecodeError:
                print("Error reading YouTube metadata JSON file")

    metadata.update({
        "resolution": exif_data.get("Image Size", exif_data.get("Video Size", "N/A")),
        "file_format": exif_data.get("File Type", exif_data.get("MIME Type", "N/A")),
        "codecs": f"{exif_data.get('Video Codec', exif_data.get('Compression', 'N/A'))}, {exif_data.get('Audio Codec', exif_data.get('Audio Format', 'N/A'))}",
        "file_size": exif_data.get("File Size", "N/A"),
        "frame_rate": exif_data.get("Video Frame Rate", exif_data.get("Frame Rate", "N/A")),
        "bit_rate": exif_data.get("Avg Bitrate", exif_data.get("Bit Rate", "N/A"))
    })

    return metadata

def main():
    os.makedirs(output_dir, exist_ok=True)
    video_page_url = get_user_url()
    video_file, yt_json_file = download_video(video_page_url)
    
    if not video_file or not yt_json_file:
        print("Failed to download video. Exiting.")
        return

    exif_data = extract_exif_metadata(video_file)
    metadata = compile_metadata(yt_json_file, exif_data)
    metadata["video_file"] = video_file

    with open(os.path.join(output_dir, json_output_file), "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata saved to {os.path.join(output_dir, json_output_file)}")
    print(f"Video saved to {video_file}")

if __name__ == "__main__":
    main()