import asyncio
import os
import re
import aiohttp
from crawl4ai import AsyncWebCrawler, BrowserConfig
from bs4 import BeautifulSoup

SITEMAP_URL = "https://docs.sentiance.com/sitemap.xml"
DOMAIN = "docs.sentiance.com"
OUTPUT_DIR = "scraped_site"

async def fetch_sitemap_urls(initial_sitemap_url):
    """
    Fetches and parses a sitemap, handling nested sitemap index files,
    to extract all unique page URLs.
    """
    print(f"Starting sitemap discovery from {initial_sitemap_url}")
    all_page_urls = set()
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

                    # If it's a URL set, add the page URLs to our final list
                    for loc in soup.find_all('url'):
                        page_url = loc.find('loc').get_text()
                        if DOMAIN in page_url:
                            all_page_urls.add(page_url.split('#')[0])
            except aiohttp.ClientError as e:
                print(f"Error during aiohttp request for {sitemap_url}: {e}")

    print(f"Found {len(all_page_urls)} unique URLs across all sitemaps.")
    return all_page_urls

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
    """Crawls a site using URLs from its sitemap and saves the content."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    browser_config = BrowserConfig(browser_type="chrome", headless=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        to_crawl = await fetch_sitemap_urls(SITEMAP_URL)
        
        for url in to_crawl:
            print(f"Crawling: {url}")
            try:
                result = await crawler.arun(url)
                
                filename = sanitize_filename(result.url)
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(result.markdown.raw_markdown)
                print(f"Saved content to {filepath}")
            except Exception as e:
                print(f"Error crawling {url}: {e}")

        print(f"\nScraping complete. Scraped {len(to_crawl)} pages from the sitemap.")

if __name__ == "__main__":
    asyncio.run(crawl_from_sitemap())