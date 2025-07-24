import json
import subprocess
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuration
video_page_url = "https://edition.cnn.com/2025/07/16/world/video/maynard-gaza-hospitals-nada-bashir-digvid"  # Replace with actual webpage URL
output_dir = "video_output"  # Directory to save video and metadata
json_output_file = "video_metadata.json"  # Output metadata file
exif_output_file = "exif_output.txt"  # Temporary ExifTool output
exiftool_path = r"C:\Users\diana\Desktop\minute.ly\exiftool-13.32_64\exiftool.exe"  # ExifTool path

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Step 1: Attempt to extract video URL with yt-dlp
def get_video_url(page_url):
    try:
        result = subprocess.run(
            ["yt-dlp", "--get-url", page_url],
            capture_output=True,
            text=True,
            check=True
        )
        video_url = result.stdout.strip()
        print(f"Video URL extracted: {video_url}")
        return video_url
    except subprocess.CalledProcessError:
        print("yt-dlp failed to extract video URL. Attempting to scrape webpage...")
        return scrape_video_url(page_url)

# Step 2: Scrape webpage for video URL if yt-dlp fails
def scrape_video_url(page_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        video_tags = soup.find_all("video")
        for video in video_tags:
            if src := video.get("src"):
                return urljoin(page_url, src)
            for source in video.find_all("source"):
                if src := source.get("src"):
                    return urljoin(page_url, src)
        
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if href.endswith((".mp4", ".m3u8", ".webm")):
                return urljoin(page_url, href)
        
        print("No video URL found via scraping.")
        return None
    except requests.RequestException as e:
        print(f"Error scraping webpage: {e}")
        return None

# Step 3: Download video and extract web metadata with yt-dlp
def download_video_and_metadata(video_url):
    try:
        subprocess.run(
            [
                "yt-dlp",
                "--write-info-json",
                "--output", f"{output_dir}/video.%(ext)s",
                video_url
            ],
            check=True
        )
        for file in os.listdir(output_dir):
            if file.endswith((".mp4", ".webm", ".mkv", ".mov")):
                return f"{output_dir}/{file}", f"{output_dir}/video.info.json"
        print("Video file not found after download.")
        return None, None
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e}")
        return None, None

# Step 4: Extract file metadata with ExifTool
def extract_exif_metadata(video_file):
    try:
        subprocess.run(
            [exiftool_path, "-a", "-G", video_file, ">", exif_output_file],
            shell=True,
            check=True
        )
        exif_data = {}
        with open(exif_output_file, "r") as f:
            for line in f:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    exif_data[key.strip()] = value.strip()
        return exif_data
    except subprocess.CalledProcessError as e:
        print(f"Error extracting ExifTool metadata: {e}")
        return {}

# Step 5: Combine metadata and output to JSON
def compile_metadata(yt_json_file, exif_data):
    metadata = {
        "title": "N/A",
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
        "video_file": "N/A"
    }

    if yt_json_file and os.path.exists(yt_json_file):
        with open(yt_json_file, "r") as f:
            yt_data = json.load(f)
            metadata.update({
                "title": yt_data.get("title", "N/A"),
                "publication_date": yt_data.get("upload_date", "N/A"),
                "categories_tags": yt_data.get("tags", ["N/A"]),
                "duration": yt_data.get("duration_string", metadata["duration"]),
                "author_uploader": yt_data.get("uploader", "N/A"),
                "view_count": str(yt_data.get("view_count", "N/A"))
            })

    metadata.update({
        "resolution": exif_data.get("Image Size", "N/A"),
        "file_format": exif_data.get("File Type", "N/A"),
        "codecs": f"{exif_data.get('Video Codec', exif_data.get('Compressor ID', 'N/A'))}, {exif_data.get('Audio Codec', exif_data.get('Audio Format', 'N/A'))}",
        "file_size": exif_data.get("File Size", "N/A"),
        "frame_rate": exif_data.get("Video Frame Rate", "N/A"),
        "bit_rate": exif_data.get("Avg Bitrate", "N/A")
    })

    return metadata

# Main execution
def main():
    video_url = get_video_url(video_page_url)
    if not video_url:
        print("Failed to extract video URL. Exiting.")
        return

    video_file, yt_json_file = download_video_and_metadata(video_url)
    if not video_file or not yt_json_file:
        print("Failed to download video or metadata. Exiting.")
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