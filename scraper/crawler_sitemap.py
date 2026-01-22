import asyncio
import os
import re
from datetime import datetime
import aiohttp
from crawl4ai import AsyncWebCrawler, BrowserConfig
from bs4 import BeautifulSoup

SITEMAP_URL = "https://docs.sentiance.com/sitemap.xml"
DOMAIN = "docs.sentiance.com"
OUTPUT_DIR = "scraped_site"

async def fetch_sitemap_urls(initial_sitemap_url):
    """
    Fetches and parses a sitemap, handling nested sitemap index files,
    to extract all unique page URLs and their last modification dates.
    """
    print(f"Starting sitemap discovery from {initial_sitemap_url}")
    url_metadata = {} # URL -> LastMod ISO String
    sitemaps_to_process = {initial_sitemap_url}
    processed_sitemaps = set()

    # Disable SSL verification for local development
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        while sitemaps_to_process:
            sitemap_url = sitemaps_to_process.pop()
            if sitemap_url in processed_sitemaps:
                continue

            print(f"Fetching sitemap: {sitemap_url}")
            processed_sitemaps.add(sitemap_url)

            try:
                async with session.get(sitemap_url) as response:
                    if response.status != 200:
                        print(f"Error fetching sitemap {sitemap_url}: Status {response.status}")
                        continue
                    content = await response.text()
                    soup = BeautifulSoup(content, "xml")

                    # If it's a sitemap index, add the nested sitemaps to the queue
                    for loc in soup.find_all('sitemap'):
                        sitemaps_to_process.add(loc.find('loc').get_text())

                    # If it's a URL set, add the page URLs and their lastmod dates
                    for url_node in soup.find_all('url'):
                        loc_node = url_node.find('loc')
                        if not loc_node:
                            continue
                        
                        page_url = loc_node.get_text().split('#')[0]
                        if DOMAIN in page_url:
                            lastmod_node = url_node.find('lastmod')
                            lastmod = lastmod_node.get_text() if lastmod_node else None
                            url_metadata[page_url] = lastmod

            except aiohttp.ClientError as e:
                print(f"Error during aiohttp request for {sitemap_url}: {e}")

    print(f"Found {len(url_metadata)} unique URLs across all sitemaps.")
    return url_metadata

def sanitize_filename(url):
    """Creates a safe filename from a URL to save the content."""
    if url.startswith(f"https://{DOMAIN}"):
        path = url[len(f"https://{DOMAIN}"):]
    else:
        path = url

    # If path is empty or just a slash (for the root URL), use 'index'
    if not path or path == '/':
        return 'index.md'

    # Replace slashes with underscores and remove invalid characters
    filename = re.sub(r'[^a-zA-Z0-9_-]', '', path.replace('/', '_'))
    return f"{filename}.md"

async def crawl_from_sitemap():
    """Crawls a site using URLs from its sitemap and saves the content conditionally."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    browser_config = BrowserConfig(browser_type="chrome", headless=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        url_metadata = await fetch_sitemap_urls(SITEMAP_URL)
        
        for url, lastmod_str in url_metadata.items():
            filename = sanitize_filename(url)
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # Conditional check
            if os.path.exists(filepath):
                # Get local file modified time (UTC proxy)
                local_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if lastmod_str:
                    try:
                        # Parse lastmod (e.g., 2024-11-05T08:20:58.498Z)
                        server_lastmod = datetime.fromisoformat(lastmod_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        
                        if server_lastmod <= local_mtime:
                            print(f"Skipping (Up to date): {url}")
                            continue
                    except ValueError:
                        print(f"Warning: Could not parse lastmod '{lastmod_str}' for {url}. Crawling anyway.")
            
            print(f"Crawling: {url}")
            try:
                result = await crawler.arun(url)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"Source: {url}\n\n")
                    f.write(result.markdown.raw_markdown)
                print(f"Saved content to {filepath}")
            except Exception as e:
                print(f"Error crawling {url}: {e}")

        print(f"\nScraping complete. Processed {len(url_metadata)} pages from the sitemap.")

if __name__ == "__main__":
    asyncio.run(crawl_from_sitemap())