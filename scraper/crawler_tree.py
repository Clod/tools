import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig
from bs4 import BeautifulSoup

START_URL = "https://docs.sentiance.com/"
DOMAIN = "docs.sentiance.com"

async def extract_links(result):
    # Extract all <a href> from page, filter to same-domain, not already crawled
    soup = BeautifulSoup(result.html, "html.parser")
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/'):
            href = f"https://{DOMAIN}{href}"
        if DOMAIN in href and href.startswith('http'):
            links.add(href.split('#')[0])  # Remove anchor links
    return links

async def crawl_site(start_url, max_pages=100):
    browser_config = BrowserConfig(
        browser_type="chrome", 
        headless=True, 
        verbose=True
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawled = set()
        to_crawl = set([start_url])
        results = []

        while to_crawl and len(crawled) < max_pages:
            # Get one URL to crawl
            url = to_crawl.pop()
            print(f"Crawling: {url} | Pages crawled: {len(crawled)} | Pages to crawl: {len(to_crawl)}")
            try:
                # Run browser with JS enabled; waits for page load
                result = await crawler.arun(url)
                results.append(result)
                crawled.add(url)

                # Extract and queue new links
                links = await extract_links(result)
                for link in links:
                    if link not in crawled and link not in to_crawl:
                        to_crawl.add(link)
            except Exception as e:
                print(f"Error crawling {url}: {e}")

        # Save markdown/html of each page
        for res in results:
            soup = BeautifulSoup(res.html, "html.parser")
            title = soup.title.string if soup.title else 'untitled'
            fname = f"{title.replace(' ', '_')}.md"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(res.markdown.raw_markdown)
        print("Scraped", len(results), "pages.")

if __name__ == "__main__":
    asyncio.run(crawl_site(START_URL))
