#!/usr/bin/env python3
"""
App Store Scraper - Extracts app metadata and screenshots from Apple App Store.

Usage:
    python scrape_app_store.py <app_store_url> <output_dir>

Example:
    python scrape_app_store.py "https://apps.apple.com/us/app/slack/id618783545" ./output
"""

import sys
import json
import re
import urllib.request
import urllib.error
import os
from html.parser import HTMLParser
from datetime import datetime


class AppStoreParser(HTMLParser):
    """Parse App Store HTML to extract app metadata."""

    def __init__(self):
        super().__init__()
        self.data = {
            'title': None,
            'subtitle': None,
            'description': None,
            'rating': None,
            'rating_count': None,
            'category': None,
            'price': None,
            'developer': None,
            'screenshots': [],
            'icon_url': None,
            'version': None,
            'size': None,
            'age_rating': None,
            'languages': None,
            'whats_new': None,
        }
        self._in_script = False
        self._script_content = []
        self._current_tag = None
        self._current_attrs = {}

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        self._current_attrs = dict(attrs)

        if tag == 'script':
            self._in_script = True
            self._script_content = []

        # Extract screenshots from picture/source elements
        if tag == 'source':
            srcset = self._current_attrs.get('srcset', '')
            # Look for screenshot URLs in srcset
            if 'is-scaled' not in self._current_attrs.get('class', ''):
                if '/static/' not in srcset and srcset:
                    # Parse srcset to get highest resolution
                    urls = self._parse_srcset(srcset)
                    if urls:
                        self.data['screenshots'].extend(urls)

        # Also check img tags for screenshots
        if tag == 'img':
            src = self._current_attrs.get('src', '')
            if 'screenshot' in src.lower() or '/screenshots/' in src.lower():
                self.data['screenshots'].append(src)

    def handle_endtag(self, tag):
        if tag == 'script' and self._in_script:
            self._in_script = False
            script_text = ''.join(self._script_content)
            self._parse_json_ld(script_text)
        self._current_tag = None

    def handle_data(self, data):
        if self._in_script:
            self._script_content.append(data)

    def _parse_srcset(self, srcset):
        """Parse srcset attribute to extract URLs."""
        urls = []
        parts = srcset.split(',')
        for part in parts:
            part = part.strip()
            if part:
                # srcset format: "url width" or just "url"
                url = part.split()[0] if ' ' in part else part
                if url and url.startswith('http'):
                    urls.append(url)
        return urls

    def _parse_json_ld(self, script_text):
        """Parse JSON-LD structured data from script tag."""
        if 'application/ld+json' not in str(self._current_attrs):
            # Try to find embedded JSON data
            if '"@type"' in script_text or '"name"' in script_text:
                try:
                    # Look for JSON object
                    match = re.search(r'\{[^{}]*"@type"[^{}]*\}', script_text, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        self._extract_from_json(data)
                except (json.JSONDecodeError, AttributeError):
                    pass
            return

        try:
            data = json.loads(script_text)
            self._extract_from_json(data)
        except json.JSONDecodeError:
            pass

    def _extract_from_json(self, data):
        """Extract relevant fields from JSON data."""
        if isinstance(data, list):
            for item in data:
                self._extract_from_json(item)
            return

        if not isinstance(data, dict):
            return

        if data.get('@type') == 'SoftwareApplication' or data.get('@type') == 'MobileApplication':
            self.data['title'] = self.data['title'] or data.get('name')
            self.data['description'] = self.data['description'] or data.get('description')
            self.data['category'] = self.data['category'] or data.get('applicationCategory')
            self.data['price'] = self.data['price'] or data.get('offers', {}).get('price')

            # Rating
            rating = data.get('aggregateRating', {})
            self.data['rating'] = self.data['rating'] or rating.get('ratingValue')
            self.data['rating_count'] = self.data['rating_count'] or rating.get('ratingCount')

            # Icon
            self.data['icon_url'] = self.data['icon_url'] or data.get('image')

            # Developer/Author
            author = data.get('author', {})
            if isinstance(author, dict):
                self.data['developer'] = self.data['developer'] or author.get('name')
            elif isinstance(author, str):
                self.data['developer'] = self.data['developer'] or author


def extract_app_id(url):
    """Extract app ID from App Store URL."""
    match = re.search(r'/id(\d+)', url)
    return match.group(1) if match else None


def fetch_page(url):
    """Fetch HTML content from URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        sys.exit(1)


def fetch_itunes_api(app_id, country='us'):
    """Fetch app data from iTunes API (more reliable for metadata)."""
    api_url = f"https://itunes.apple.com/lookup?id={app_id}&country={country}"

    try:
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('resultCount', 0) > 0:
                return data['results'][0]
    except Exception as e:
        print(f"Warning: iTunes API lookup failed: {e}")
    return None


def download_image(url, filepath):
    """Download an image from URL to filepath."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False


def scrape_app_store(url, output_dir):
    """Main function to scrape App Store data."""

    # Extract app ID
    app_id = extract_app_id(url)
    if not app_id:
        print("Error: Could not extract app ID from URL")
        sys.exit(1)

    print(f"Fetching app data for ID: {app_id}")

    # Fetch from iTunes API (primary source - more reliable)
    api_data = fetch_itunes_api(app_id)

    # Also fetch HTML page for any additional data
    html = fetch_page(url)
    parser = AppStoreParser()
    parser.feed(html)
    parsed_data = parser.data

    # Merge data, preferring API data
    app_data = {
        'url': url,
        'app_id': app_id,
        'title': api_data.get('trackName') if api_data else parsed_data['title'],
        'subtitle': api_data.get('subtitle', '') if api_data else parsed_data.get('subtitle', ''),
        'description': api_data.get('description') if api_data else parsed_data['description'],
        'rating': api_data.get('averageUserRating') if api_data else parsed_data['rating'],
        'rating_count': api_data.get('userRatingCount') if api_data else parsed_data['rating_count'],
        'category': api_data.get('primaryGenreName') if api_data else parsed_data['category'],
        'price': api_data.get('formattedPrice', 'Free') if api_data else (parsed_data['price'] or 'Free'),
        'developer': api_data.get('artistName') if api_data else parsed_data['developer'],
        'developer_url': api_data.get('artistViewUrl') if api_data else None,
        'icon_url': api_data.get('artworkUrl512') if api_data else parsed_data['icon_url'],
        'screenshots': api_data.get('screenshotUrls', []) if api_data else parsed_data['screenshots'],
        'ipad_screenshots': api_data.get('ipadScreenshotUrls', []) if api_data else [],
        'version': api_data.get('version') if api_data else parsed_data.get('version'),
        'size_bytes': api_data.get('fileSizeBytes') if api_data else None,
        'minimum_os_version': api_data.get('minimumOsVersion') if api_data else None,
        'age_rating': api_data.get('contentAdvisoryRating') if api_data else parsed_data.get('age_rating'),
        'languages': api_data.get('languageCodesISO2A', []) if api_data else [],
        'release_date': api_data.get('releaseDate') if api_data else None,
        'current_version_release_date': api_data.get('currentVersionReleaseDate') if api_data else None,
        'release_notes': api_data.get('releaseNotes') if api_data else parsed_data.get('whats_new'),
        'seller_name': api_data.get('sellerName') if api_data else None,
        'bundle_id': api_data.get('bundleId') if api_data else None,
        'genres': api_data.get('genres', []) if api_data else [],
        'in_app_purchases': api_data.get('isVppDeviceBasedLicensingEnabled', False) if api_data else False,
        'scraped_at': datetime.utcnow().isoformat() + 'Z',
    }

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    screenshots_dir = os.path.join(output_dir, 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)

    # Download screenshots
    screenshot_files = []
    all_screenshots = app_data['screenshots'] + app_data.get('ipad_screenshots', [])

    # Deduplicate screenshots
    seen = set()
    unique_screenshots = []
    for url in all_screenshots:
        if url not in seen:
            seen.add(url)
            unique_screenshots.append(url)

    print(f"Downloading {len(unique_screenshots)} screenshots...")
    for i, screenshot_url in enumerate(unique_screenshots, 1):
        ext = 'png' if '.png' in screenshot_url.lower() else 'jpg'
        filename = f"screenshot_{i:02d}.{ext}"
        filepath = os.path.join(screenshots_dir, filename)

        if download_image(screenshot_url, filepath):
            screenshot_files.append(filename)
            print(f"  Downloaded: {filename}")

    # Download icon
    if app_data['icon_url']:
        icon_path = os.path.join(output_dir, 'icon.png')
        if download_image(app_data['icon_url'], icon_path):
            print("  Downloaded: icon.png")
            app_data['icon_local'] = 'icon.png'

    # Update app_data with local screenshot paths
    app_data['screenshot_files'] = screenshot_files

    # Generate slug for filenames
    slug = re.sub(r'[^a-z0-9]+', '-', app_data['title'].lower()).strip('-') if app_data['title'] else 'app'

    # Save JSON output
    json_path = os.path.join(output_dir, f"{slug}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(app_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved JSON: {json_path}")

    # Generate Markdown report
    md_content = generate_markdown_report(app_data, screenshots_dir)
    md_path = os.path.join(output_dir, f"{slug}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Saved Markdown: {md_path}")

    return app_data


def format_size(size_bytes):
    """Format file size in human readable format."""
    if not size_bytes:
        return "Unknown"
    try:
        size = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except (ValueError, TypeError):
        return "Unknown"


def generate_markdown_report(data, screenshots_dir):
    """Generate a Markdown report from app data."""

    lines = [
        f"# {data['title']}",
        "",
    ]

    if data.get('subtitle'):
        lines.extend([f"*{data['subtitle']}*", ""])

    lines.extend([
        "## Overview",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| **Developer** | {data.get('developer', 'N/A')} |",
        f"| **Category** | {data.get('category', 'N/A')} |",
        f"| **Price** | {data.get('price', 'Free')} |",
        f"| **Rating** | {data.get('rating', 'N/A'):.1f}/5 ({data.get('rating_count', 0):,} ratings) |" if data.get('rating') else f"| **Rating** | N/A |",
        f"| **Version** | {data.get('version', 'N/A')} |",
        f"| **Size** | {format_size(data.get('size_bytes'))} |",
        f"| **Age Rating** | {data.get('age_rating', 'N/A')} |",
        f"| **Minimum iOS** | {data.get('minimum_os_version', 'N/A')} |",
        "",
    ])

    if data.get('genres'):
        lines.extend([
            "### Categories",
            "",
            ", ".join(data['genres']),
            "",
        ])

    lines.extend([
        "## Description",
        "",
        data.get('description', 'No description available.'),
        "",
    ])

    if data.get('release_notes'):
        lines.extend([
            "## What's New",
            "",
            data['release_notes'],
            "",
        ])

    if data.get('screenshot_files'):
        lines.extend([
            "## Screenshots",
            "",
        ])
        for filename in data['screenshot_files']:
            lines.append(f"![Screenshot](screenshots/{filename})")
        lines.append("")

    if data.get('languages'):
        lines.extend([
            "## Languages",
            "",
            ", ".join(data['languages'][:20]),  # Limit to first 20
            "",
        ])

    lines.extend([
        "## Links",
        "",
        f"- [App Store]({data['url']})",
    ])

    if data.get('developer_url'):
        lines.append(f"- [Developer]({data['developer_url']})")

    lines.extend([
        "",
        "---",
        f"*Scraped at: {data.get('scraped_at', 'Unknown')}*",
    ])

    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: python scrape_app_store.py <app_store_url> <output_dir>")
        print("\nExample:")
        print('  python scrape_app_store.py "https://apps.apple.com/us/app/slack/id618783545" ./output')
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2]

    if 'apps.apple.com' not in url:
        print("Error: URL must be an Apple App Store URL (apps.apple.com)")
        sys.exit(1)

    scrape_app_store(url, output_dir)
    print("\nDone!")


if __name__ == "__main__":
    main()
