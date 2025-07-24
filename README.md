Video Extraction

A Python script to download videos from a user-provided webpage URL, extract metadata using yt-dlp and ExifTool, and save the results to a JSON file.

Features





Prompts the user to input a webpage URL containing an embedded video.



Extracts the video URL using yt-dlp or web scraping with BeautifulSoup.



Downloads the video using yt-dlp with FFmpeg for stream merging.



Extracts file metadata (e.g., resolution, codecs) using ExifTool.



Combines web and file metadata into a JSON file.

Prerequisites





Python 3.11+: Installed via Chocolatey (python311 in C:\ProgramData\chocolatey\lib).



FFmpeg: Installed via Chocolatey (ffmpeg -version).



ExifTool: Located at exiftool-13.32_64\exiftool.exe in the project directory.



Python Packages:





yt-dlp



requests



beautifulsoup4

Setup





Clone the Repository:

git clone https://github.com/diana2granat/video_extraction.git
cd video_extraction



Create and Activate a Virtual Environment:

python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows



Install Python Packages:

pip install yt-dlp requests beautifulsoup4



Install FFmpeg (if not already installed):

choco install ffmpeg -y  # Run in admin PowerShell



Download ExifTool:





Download exiftool-13.32_64.zip from https://exiftool.org/.



Extract to exiftool-13.32_64 in the project directory.

Usage





Run the Script:

python extract_video_metadata.py



Enter URL: When prompted, input the webpage URL (e.g., https://www.example.com/video-page).



Outputs:





Video: video_output/video.mp4 (or similar format).



Metadata: video_output/video_metadata.json.

Example Output

video_output/video_metadata.json:

{
    "title": "Sample Embedded Video",
    "publication_date": "2025-07-24",
    "categories_tags": ["Tutorial", "Tech"],
    "duration": "00:10:15",
    "author_uploader": "TechGuru",
    "view_count": "50000",
    "resolution": "1920x1080",
    "file_format": "MP4",
    "codecs": "H.264, AAC",
    "file_size": "50.2 MB",
    "frame_rate": "30 fps",
    "bit_rate": "6 Mbps",
    "video_file": "video_output/video.mp4"
}

Notes





Ensure you have permission to download videos (check the website’s terms).



For JavaScript-heavy sites, use browser developer tools (F12, Network > Media) to find direct video URLs (e.g., .mp4, .m3u8).



Update yt-dlp regularly: pip install -U yt-dlp.

License

MIT License