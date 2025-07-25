import json
import subprocess
import os
import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Configuration
output_dir = "video_output"
json_output_file = "video_metadata.json"
exif_output_file = "exif_output.txt"
exiftool_path = r"C:\Users\diana\Desktop\minute.ly\exiftool-13.32_64\exiftool.exe"
proxy = None  # Set to "http://<proxy-ip>:<port>" for Israel (Mako) or U.S. (Fox Sports) if needed

# Custom headers for different sites
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

def scrape_video_url(page_url):
    try:
        # Update Referer based on the domain
        headers = HEADERS.copy()
        if "foxsports.com" in page_url:
            headers["Referer"] = "https://www.foxsports.com/"
        elif "cnn.com" in page_url:
            headers["Referer"] = "https://edition.cnn.com/"
        elif "cbssports.com" in page_url:
            headers["Referer"] = "https://www.cbssports.com/"

        # Try basic requests first
        response = requests.get(page_url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for <source> tag with MP4 URL (Mako)
        source_tag = soup.find('source', type='video/mp4')
        if source_tag and 'src' in source_tag.attrs:
            video_url = source_tag['src']
            if video_url.startswith('http'):
                print(f"Found MP4 URL: {video_url}")
                return video_url
            elif video_url.startswith('//'):
                video_url = 'https:' + video_url
                print(f"Found MP4 URL: {video_url}")
                return video_url
        
        # If <source> tag not found, try Selenium
        print("No video URL found with requests. Trying Selenium...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
        chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL errors
        chrome_options.add_argument("--allow-insecure-localhost")
        if proxy:
            chrome_options.add_argument(f"--proxy-server={proxy}")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(page_url)
        time.sleep(5)  # Increased wait time for JavaScript to load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        # Try <source> tag again
        source_tag = soup.find('source', type='video/mp4')
        if source_tag and 'src' in source_tag.attrs:
            video_url = source_tag['src']
            if video_url.startswith('http'):
                print(f"Found MP4 URL with Selenium: {video_url}")
                return video_url
            elif video_url.startswith('//'):
                video_url = 'https:' + video_url
                print(f"Found MP4 URL with Selenium: {video_url}")
                return video_url
        
        # Look for Mako videoID (fallback)
        video_id_match = re.search(r'videoID:\s*["\'](\d+)["\']', soup.text)
        if video_id_match:
            video_id = video_id_match.group(1)
            print(f"Found Mako video ID: {video_id}")
            return f"https://keshethlslive-lh.akamaihd.net/i/{video_id}_@319237/index_700_av-p.m3u8"
        
        # Look for JW Player data-video-id (Fox Sports)
        jw_player = soup.find('div', class_='fs-video-player', attrs={'data-video-id': True})
        if jw_player and 'data-video-id' in jw_player.attrs:
            video_id = jw_player['data-video-id']
            print(f"Found JW Player video ID: {video_id}")
            jw_config_url = f"https://cdn.jwplayer.com/v2/media/{video_id}"
            try:
                jw_response = requests.get(jw_config_url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None)
                jw_response.raise_for_status()
                jw_data = jw_response.json()
                if 'playlist' in jw_data and jw_data['playlist']:
                    video_url = jw_data['playlist'][0].get('file')
                    print(f"Found JW Player video URL: {video_url}")
                    return video_url
            except Exception as e:
                print(f"Error fetching JW Player config: {e}")
        
        print("No video URL found in page source.")
        return None
    except Exception as e:
        print(f"Error scraping video URL: {e}")
        try:
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(soup.text if 'soup' in locals() else response.text)
            print("Page source saved to page_source.html for debugging.")
        except:
            print("Could not save page source.")
        return None

def scrape_webpage_metadata(page_url):
    try:
        headers = HEADERS.copy()
        if "foxsports.com" in page_url:
            headers["Referer"] = "https://www.foxsports.com/"
        elif "cnn.com" in page_url:
            headers["Referer"] = "https://edition.cnn.com/"
        elif "cbssports.com" in page_url:
            headers["Referer"] = "https://www.cbssports.com/"

        response = requests.get(page_url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text.strip() if soup.find('title') else "N/A"
        description = soup.find('meta', attrs={'name': 'description'})['content'].strip() if soup.find('meta', attrs={'name': 'description'}) else "N/A"
        return {"title": title, "description": description}
    except Exception as e:
        print(f"Error scraping webpage metadata: {e}")
        return {"title": "N/A", "description": "N/A"}

def download_video(page_url):
    # Check if the URL is a direct video URL
    if page_url.endswith(('.mp4', '.m3u8', '.webm', '.mkv', '.flv')):
        video_url = page_url
    else:
        # Scrape the webpage for the video URL
        video_url = scrape_video_url(page_url)
        if not video_url:
            print("No video URL found. Prompting for manual URL input...")
            video_url = input("Enter the direct video URL (e.g., .mp4 or .m3u8) or press Enter to try generic download: ").strip()
            if not video_url:
                print("No manual URL provided. Attempting generic download.")
                video_url = page_url
    
    # Update headers for yt-dlp based on domain
    headers = HEADERS.copy()
    if "foxsports.com" in page_url:
        headers["Referer"] = "https://www.foxsports.com/"
    elif "cnn.com" in page_url:
        headers["Referer"] = "https://edition.cnn.com/"
    elif "cbssports.com" in page_url:
        headers["Referer"] = "https://www.cbssports.com/"

    try:
        # Add cookies
        cookies = requests.get(page_url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None).cookies.get_dict()
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()]) if cookies else ""
        
        cmd = [
            "yt-dlp",
            "--no-check-certificate",
            "--ignore-errors",
            "--write-info-json",
            "--write-description",
            "--write-thumbnail",
            "--all-subs",
            "--convert-subs", "srt",
            "--user-agent", headers["User-Agent"],
            "--referer", headers["Referer"],
            "--output", f"{output_dir}/video_%(id)s.%(ext)s",
        ]
        if proxy:
            cmd.extend(["--proxy", proxy])
        if cookie_string:
            cmd.extend(["--add-header", f"Cookie: {cookie_string}"])
        cmd.append(video_url)
        
        subprocess.run(cmd, check=True)
        
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
        
        with open(exif_output_file, "w", encoding="utf-8") as f:
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

def compile_metadata(yt_json_file, exif_data, page_url=None):
    metadata = {
        "source_url": page_url or "N/A",
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

    if page_url:
        webpage_metadata = scrape_webpage_metadata(page_url)
        metadata.update({
            "title": webpage_metadata["title"],
            "description": webpage_metadata["description"]
        })

    if yt_json_file and os.path.exists(yt_json_file):
        with open(yt_json_file, "r", encoding="utf-8") as f:
            try:
                yt_data = json.load(f)
                metadata.update({
                    "source_url": yt_data.get("webpage_url", page_url or "N/A"),
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
    page_url = get_user_url()
    video_file, yt_json_file = download_video(page_url)
    
    if not video_file or not yt_json_file:
        print("Failed to download video. Exiting.")
        return

    exif_data = extract_exif_metadata(video_file)
    metadata = compile_metadata(yt_json_file, exif_data, page_url)
    metadata["video_file"] = video_file

    with open(os.path.join(output_dir, json_output_file), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    print(f"Metadata saved to {os.path.join(output_dir, json_output_file)}")
    print(f"Video saved to {video_file}")

if __name__ == "__main__":
    main()