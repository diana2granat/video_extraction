# Video Extraction Tool

A Python script to download videos from webpages and extract comprehensive metadata using `yt-dlp` and `ExifTool`.

## Solution Overview

I consulted Grok to identify the optimal solution:

| Component       | Advantage                                                                 |
|-----------------|---------------------------------------------------------------------------|
| **Python**      | Versatile with libraries for web scraping, JSON handling, and subprocess execution |
| **yt-dlp**      | Extracts video URLs and metadata from thousands of websites               |
| **ExifTool**    | Provides detailed file metadata (resolution, codecs, etc.)                |
| **JSON Output** | Structured format easily convertible to CSV or other formats              |

## Features

✔ **URL Input** - Prompts for webpage URL with embedded video  
✔ **Smart Extraction** - Uses `yt-dlp` or BeautifulSoup for video URL detection  
✔ **Reliable Download** - Leverages `yt-dlp` with FFmpeg for stream merging  
✔ **Rich Metadata** - Combines web and file metadata into unified JSON output  
✔ **Cross-Platform** - Works on Windows, macOS, and Linux  

## Prerequisites

### Required Software
- **Python 3.11+** (`python311` via Chocolatey)
- **FFmpeg** (`choco install ffmpeg -y`)
- **ExifTool** ([Download](https://exiftool.org/))

### Python Packages
```bash
yt-dlp
requests
beautifulsoup4
selenium