import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse, urljoin
import os
import json
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import re
import jsbeautifier
import cssbeautifier
from playwright.async_api import async_playwright
import ast

class EnhancedDownloaderSpider(scrapy.Spider):
    name = 'scraper'
    
    def __init__(self, start_url=None, max_depth=1000, *args, **kwargs):
        super(EnhancedDownloaderSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.link_extractor = LinkExtractor()
        self.downloaded_urls = set()
        self.max_depth = max_depth
        self.total_characters = 0
        self.api_endpoints = set()

    def parse(self, response, depth=0):
        url = response.url
        if url in self.downloaded_urls or depth > self.max_depth:
            return
        self.downloaded_urls.add(url)

        # Save the main content
        self.save_content(response)

        # Extract and download all linked resources
        yield from self.extract_and_download_resources(response)

        # Extract potential API endpoints
        self.extract_api_endpoints(response)

        # Extract and follow links
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse, cb_kwargs={'depth': depth + 1})

    def save_content(self, response):
        url_path = urlparse(response.url).path
        if url_path == '' or url_path.endswith('/'):
            url_path += 'index.html'
        elif '.' not in url_path.split('/')[-1]:
            url_path += '/index.html'

        file_path = os.path.join('downloaded_content', self.allowed_domains[0], url_path.lstrip('/'))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(response.body)
        
        # Count characters
        self.total_characters += len(response.text)

    def extract_and_download_resources(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all src, href, and data-src attributes
        resources = []
        for tag in soup.find_all():
            for attr in ['src', 'href', 'data-src']:
                if tag.has_attr(attr):
                    resources.append(urljoin(response.url, tag[attr]))

        # Download resources
        for resource_url in set(resources):
            yield scrapy.Request(resource_url, callback=self.save_resource)

    def save_resource(self, response):
        url_path = urlparse(response.url).path
        if url_path == '' or url_path.endswith('/'):
            url_path += 'index.html'
        elif '.' not in url_path.split('/')[-1]:
            url_path += '/index.html'

        file_path = os.path.join('downloaded_content', self.allowed_domains[0], url_path.lstrip('/'))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        content = response.body
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()

        # Beautify JavaScript and CSS
        if 'javascript' in content_type:
            content = jsbeautifier.beautify(content.decode('utf-8')).encode('utf-8')
        elif 'css' in content_type:
            content = cssbeautifier.beautify(content.decode('utf-8')).encode('utf-8')

        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Count characters for text-based files, I added it so you can calculate how many tokens will be used. lol 1 token = 4 characters
        if 'text' in content_type or 'javascript' in content_type or 'css' in content_type:
            self.total_characters += len(content.decode('utf-8'))

    def extract_api_endpoints(self, response):
        # Extract potential API endpoints from JavaScript
        js_pattern = re.compile(r'(?:get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]')
        matches = js_pattern.findall(response.text)
        for match in matches:
            if match.startswith('/') or match.startswith('http'):
                self.api_endpoints.add(match)

    def closed(self, reason):
        print(f"Total characters downloaded: {self.total_characters}")
        print(f"Potential API endpoints found: {len(self.api_endpoints)}")
        with open('api_endpoints.json', 'w') as f:
            json.dump(list(self.api_endpoints), f, indent=2)

async def download_dynamic_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        
        # Wait for dynamic content to load
        await page.wait_for_timeout(5000)

        # Scroll to bottom to trigger lazy loading
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(2000)

        content = await page.content()
        
        # Extract and save WebSocket traffic
        websocket_messages = await page.evaluate('''
            () => {
                return window._websocketMessages || [];
            }
        ''')
        
        with open('websocket_traffic.json', 'w') as f:
            json.dump(websocket_messages, f, indent=2)

        await browser.close()

    return content

def extract_and_save_code(content, base_path):
    # Extract inline JavaScript
    script_pattern = re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL)
    scripts = script_pattern.findall(content)

    # Extract inline CSS
    style_pattern = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL)
    styles = style_pattern.findall(content)

    total_characters = 0

    # Save extracted code
    for i, script in enumerate(scripts):
        beautified_js = jsbeautifier.beautify(script)
        with open(f'{base_path}/inline_script_{i}.js', 'w') as f:
            f.write(beautified_js)
        total_characters += len(beautified_js)

        # Attempt to deobfuscate JavaScript
        try:
            deobfuscated_js = deobfuscate_js(beautified_js)
            with open(f'{base_path}/deobfuscated_script_{i}.js', 'w') as f:
                f.write(deobfuscated_js)
            total_characters += len(deobfuscated_js)
        except Exception as e:
            print(f"Error deobfuscating script {i}: {e}")

    for i, style in enumerate(styles):
        beautified_css = cssbeautifier.beautify(style)
        with open(f'{base_path}/inline_style_{i}.css', 'w') as f:
            f.write(beautified_css)
        total_characters += len(beautified_css)

    return total_characters

def deobfuscate_js(js_code):
    # This is a basic deobfuscation attempt
    tree = ast.parse(js_code)
    deobfuscated = ast.unparse(tree)
    return deobfuscated

def count_characters_in_directory(directory):
    total_chars = 0
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_chars += len(f.read())
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
    return total_chars

async def main():
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 1,
    })

    start_url = 'https://example.com/'  # Replace with your target website
    process.crawl(EnhancedDownloaderSpider, start_url=start_url, max_depth=1000)
    process.start()

    # After the crawl is complete, download dynamic content
    dynamic_content = await download_dynamic_content(start_url)

    # Extract and save code from dynamic content
    dynamic_content_chars = extract_and_save_code(dynamic_content, 'downloaded_content')

    # Count characters in all downloaded files
    total_chars = count_characters_in_directory('downloaded_content')

    print(f"Total characters in downloaded files: {total_chars}")
    print(f"Total characters in dynamic content: {dynamic_content_chars}")
    print(f"Grand total of characters: {total_chars + dynamic_content_chars}")

if __name__ == "__main__":
    asyncio.run(main())