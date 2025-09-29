#!/usr/bin/env python3
"""
Headless Browser Spine Industry Scraper
Uses Selenium WebDriver to bypass anti-bot protection and handle JavaScript
"""

import json
import csv
from datetime import datetime
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import re
from urllib.parse import urljoin, urlparse

# Configuration
OUTPUT_DIR = "spine_industry_data"
MAX_ARTICLES_PER_SITE = 50  # Reasonable limit

# Default logging function (can be overridden by web server)
def add_log(message):
    """Default logging function - prints to console with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

# Target websites
SPINE_WEBSITES = [
    {
        'name': 'Spine Market Group',
        'url': 'https://thespinemarketgroup.com/',
        'category': 'industry_news'
    },
    {
        'name': 'Spine Market',
        'url': 'https://spine-market.com/',
        'category': 'market_research'
    },
    {
        'name': 'Ortho Spine News', 
        'url': 'https://orthospinenews.com/',
        'category': 'research_reports'
    },
    {
        'name': 'Becker\'s Spine Review',
        'url': 'https://www.beckersspine.com/',
        'category': 'healthcare_insights'
    }
]


class HeadlessSpineScraper:
    """Headless browser scraper for spine industry websites"""

    def __init__(self):
        self.driver = None
        self.scraped_articles = []
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def setup_driver(self):
        """Setup Chrome headless driver with robust error handling"""
        print("Setting up headless Chrome browser...")
        if 'add_log' in globals():
            add_log("🚀 Setting up headless Chrome browser...")

        try:
            chrome_options = Options()

            # Headless mode
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            # Anti-detection measures
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Realistic user agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36')

            # Use system PATH ChromeDriver (Method 2 - the working method)
            print("   🔍 Using system PATH ChromeDriver...")
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("   ChromeDriver setup successful!")

            self.driver = driver

            # Execute script to hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("Headless browser ready!")
            if 'add_log' in globals():
                add_log("✅ Headless browser ready!")
            return True

        except Exception as e:
            error_msg = f"Failed to setup browser: {e}"
            print(error_msg)
            print("Make sure Chrome is installed")
            if 'add_log' in globals():
                add_log(error_msg)
            return False

    def get_page_content(self, url, wait_time=10):
        """Get page content using headless browser"""
        try:
            print(f"  Loading: {url}")

            self.driver.get(url)

            # Wait for page to load
            time.sleep(random.uniform(2, 4))

            # Wait for body to be present
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Get page title
            title = self.driver.title

            # Get main content (try multiple extraction strategies)
            content = ""

            # Strategy 1: Try specific content selectors
            content_selectors = [
                'article', '.content', '.post-content', '.entry-content',
                '.main-content', 'main', '.article-body', '.post',
                '.single-content', '.the-content', '.entry',
                '[class*="content"]', '[id*="content"]'
            ]

            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        element = elements[0]
                        # Get text from this element and its children
                        content = element.text
                        if len(content) > 100:  # Lower threshold for better detection
                            break
                except:
                    continue

            # Strategy 2: Try to find content containers
            if len(content) < 100:
                try:
                    # Look for common content container patterns
                    containers = self.driver.find_elements(By.CSS_SELECTOR,
                        'div[class*="content"], div[id*="content"], div[class*="post"], div[class*="article"]')
                    for container in containers:
                        text = container.text
                        if len(text) > len(content) and len(text) > 100:
                            content = text
                except:
                    pass

            # Strategy 3: Get all meaningful text from body
            if len(content) < 100:
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    all_text = body.text

                    # Filter out navigation, footer, header content
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    meaningful_lines = []

                    for line in lines:
                        # Skip common navigation/footer patterns
                        if not any(skip in line.lower() for skip in [
                            'menu', 'navigation', 'footer', 'copyright', '©',
                            'home', 'about', 'contact', 'privacy', 'terms',
                            'login', 'register', 'search', 'skip to'
                        ]) and len(line) > 20:
                            meaningful_lines.append(line)

                    content = '\n'.join(meaningful_lines)
                except:
                    content = "Content extraction failed"

            # Final fallback: get full body text
            if len(content) < 50:
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    content = body.text[:1000]  # Limit to first 1000 chars
                except:
                    content = "Unable to extract content"

            # Get all links on the page
            article_links = []
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                base_domain = urlparse(url).netloc

                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if (href and base_domain in href and 
                            not any(skip in href for skip in ['#', 'javascript:', 'mailto:', '.jpg', '.png']) and
                            any(include in href.lower() for include in ['news', 'article', '2025', '2024', 'spine', 'medical'])):
                            article_links.append(href)
                    except:
                        continue
            except:
                pass

            return {
                'url': url,
                'title': title,
                'content': content,
                'content_length': len(content),
                'article_links': list(set(article_links))  # Remove duplicates
            }

        except TimeoutException:
            print(f"    ⏰ Timeout loading page")
            return None
        except Exception as e:
            print(f"    ❌ Error loading page: {e}")
            return None

    def extract_metadata(self, content, title):
        """Extract basic metadata from content"""
        # Extract financial mentions
        financial_patterns = [
            r'\$[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|M|B)',
            r'[0-9]+(?:\.[0-9]+)?%\s*(?:growth|increase|decrease)',
            r'CAGR\s*(?:of\s*)?[0-9]+(?:\.[0-9]+)?%'
        ]

        financial_mentions = []
        for pattern in financial_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            financial_mentions.extend(matches)

        # Extract spine procedures
        spine_procedures = [
            'fusion', 'discectomy', 'laminectomy', 'foraminotomy',
            'cervical', 'lumbar', 'thoracic', 'ACDF', 'TLIF', 'PLIF', 'ALIF',
            'disc replacement', 'navigation', 'robotic surgery'
        ]

        mentioned_procedures = []
        content_lower = content.lower()
        for procedure in spine_procedures:
            if procedure.lower() in content_lower:
                mentioned_procedures.append(procedure)

        return {
            'spine_procedures': mentioned_procedures,
            'financial_mentions': financial_mentions
        }

    def scrape_website(self, website_info):
        """Scrape a single website comprehensively"""
        name = website_info['name']
        url = website_info['url']
        category = website_info['category']

        print(f"\n🌐 SCRAPING: {name}")
        print(f"URL: {url}")
        print("=" * 60)
        if 'add_log' in globals():
            add_log(f"🌐 Starting to scrape: {name}")

        articles_data = []

        # Step 1: Get homepage content
        homepage_data = self.get_page_content(url)

        if not homepage_data:
            print(f"❌ Could not load homepage for {name}")
            return []

        print(f"  ✅ Homepage loaded: {homepage_data['content_length']:,} characters")

        # Process homepage as an article
        homepage_metadata = self.extract_metadata(homepage_data['content'], homepage_data['title'])

        homepage_article = {
            'title': homepage_data['title'],
            'url': url,
            'website_name': name,
            'category': category,
            'content': homepage_data['content'][:5000],  # Limit content
            'content_length': homepage_data['content_length'],
            'scraped_at': datetime.now().isoformat(),
            'method': 'headless_browser',
            **homepage_metadata
        }
        articles_data.append(homepage_article)

        # Step 2: Find and scrape individual articles
        article_links = homepage_data['article_links'][:MAX_ARTICLES_PER_SITE]

        print(f"  🔍 Found {len(article_links)} article links")

        if article_links:
            print(f"  📰 Scraping individual articles...")

            for i, article_url in enumerate(article_links, 1):
                print(f"    📄 {i:2d}/{len(article_links)}: {article_url[:60]}...")

                # Random delay to be respectful
                time.sleep(random.uniform(3, 7))

                article_data = self.get_page_content(article_url, wait_time=15)

                if article_data and article_data['content_length'] > 50:  # Lower threshold to catch more content
                    article_metadata = self.extract_metadata(article_data['content'], article_data['title'])

                    article_info = {
                        'title': article_data['title'],
                        'url': article_url,
                        'website_name': name,
                        'category': category,
                        'content': article_data['content'][:8000],  # Generous limit
                        'content_length': article_data['content_length'],
                        'scraped_at': datetime.now().isoformat(),
                        'method': 'headless_browser',
                        **article_metadata
                    }

                    articles_data.append(article_info)

                    # Log scraping results
                    print(f"      ✅ Scraped: {article_data['content_length']:,} chars")
                else:
                    print(f"      ⚠️  Low quality or failed")

                # Stop if we're getting too many failures
                if i >= 20:  # Reasonable limit
                    break

        print(f"\n  ✅ {name} COMPLETE: {len(articles_data)} articles scraped")
        return articles_data

    def scrape_all_websites(self):
        """Scrape all spine industry websites"""
        print("🦴 HEADLESS BROWSER SPINE INDUSTRY SCRAPER")
        print("=" * 70)
        print("Using Selenium WebDriver to bypass anti-bot protection")
        print()

        if not self.setup_driver():
            return []

        all_articles = []

        try:
            for website in SPINE_WEBSITES:
                articles = self.scrape_website(website)
                all_articles.extend(articles)

                # Summary for this website
                if articles:
                    procedures = set()
                    financial_count = 0
                    for article in articles:
                        procedures.update(article.get('spine_procedures', []))
                        if article.get('financial_mentions'):
                            financial_count += 1

                    print(f"    📊 Summary: {len(procedures)} procedures, {financial_count} financial mentions")

                # Delay between websites
                if website != SPINE_WEBSITES[-1]:  # Not the last website
                    print("    ⏳ Waiting 10 seconds before next website...")
                    time.sleep(10)

        except KeyboardInterrupt:
            print("\n⏹️  Scraping interrupted by user")
        except Exception as e:
            print(f"\n❌ Scraping error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("\n🔄 Browser closed")

        return all_articles

    def export_data(self, articles):
        """Export scraped data to multiple formats"""
        if not articles:
            print("❌ No articles to export")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export to CSV
        csv_file = os.path.join(OUTPUT_DIR, f"spine_headless_scraper_{timestamp}.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'title', 'url', 'website_name', 'category', 'content_length',
                'spine_procedures', 'financial_mentions', 'scraped_at'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for article in articles:
                writer.writerow({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'website_name': article.get('website_name', ''),
                    'category': article.get('category', ''),
                    'content_length': article.get('content_length', 0),
                    'spine_procedures': ', '.join(article.get('spine_procedures', [])),
                    'financial_mentions': ', '.join(article.get('financial_mentions', [])),
                    'scraped_at': article.get('scraped_at', '')
                })

        # Export to JSON
        json_file = os.path.join(OUTPUT_DIR, f"spine_headless_scraper_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                'scraping_date': datetime.now().isoformat(),
                'total_articles': len(articles),
                'method': 'headless_browser_selenium',
                'source_websites': [w['name'] for w in SPINE_WEBSITES],
                'articles': articles
            }, jsonfile, indent=2, ensure_ascii=False)

        # Create summary report
        summary_file = os.path.join(OUTPUT_DIR, f"headless_scraper_summary_{timestamp}.txt")
        self.create_summary_report(articles, summary_file)

        print(f"\n💾 DATA EXPORTED:")
        print(f"  📊 CSV: {csv_file}")
        print(f"  📋 JSON: {json_file}")
        print(f"  📄 Summary: {summary_file}")

    def create_summary_report(self, articles, filename):
        """Create a summary report"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("HEADLESS BROWSER SPINE INDUSTRY SCRAPING REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Scraping Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Articles: {len(articles)}\n")
            f.write(f"Method: Headless Browser (Selenium WebDriver)\n\n")

            # Analysis by website
            by_website = {}
            all_procedures = {}
            financial_count = 0
            total_content = 0

            for article in articles:
                website = article.get('website_name', 'Unknown')
                by_website[website] = by_website.get(website, 0) + 1

                for procedure in article.get('spine_procedures', []):
                    all_procedures[procedure] = all_procedures.get(procedure, 0) + 1

                if article.get('financial_mentions'):
                    financial_count += 1

                total_content += article.get('content_length', 0)

            f.write("ARTICLES BY WEBSITE:\n")
            for website, count in sorted(by_website.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {website}: {count} articles\n")

            f.write(f"\nKEY INSIGHTS:\n")
            f.write(f"  • Total articles: {len(articles)}\n")
            f.write(f"  • Financial mentions: {financial_count} articles\n")
            f.write(f"  • Unique procedures: {len(all_procedures)}\n")
            f.write(f"  • Average content: {total_content//len(articles) if articles else 0:,} characters\n")

            if all_procedures:
                f.write(f"\nTOP PROCEDURES BY MENTIONS:\n")
                sorted_procedures = sorted(all_procedures.items(), key=lambda x: x[1], reverse=True)
                for i, (procedure, mentions) in enumerate(sorted_procedures[:10], 1):
                    f.write(f"  {i:2d}. {procedure}: {mentions} mentions\n")

def main():
    """Main execution function"""
    scraper = HeadlessSpineScraper()

    print("🚀 Starting headless browser scraping...")
    print("💡 This will take 10-20 minutes but should bypass all blocking!")

    # Scrape all websites
    articles = scraper.scrape_all_websites()

    if articles:
        print(f"\n🎉 SCRAPING COMPLETE!")
        print(f"Successfully scraped {len(articles)} articles")

        # Analyze results
        procedures = set()
        financial_count = 0
        total_content = 0

        for article in articles:
            procedures.update(article.get('spine_procedures', []))
            if article.get('financial_mentions'):
                financial_count += 1
            total_content += article.get('content_length', 0)

        print(f"\n📊 FINAL ANALYSIS:")
        print(f"  • Total articles: {len(articles)}")
        print(f"  • Unique procedures: {len(procedures)}")
        print(f"  • Financial mentions: {financial_count}")
        print(f"  • Average content: {total_content//len(articles):,} characters")

        if procedures:
            print(f"  • Procedures found: {', '.join(list(procedures)[:8])}")

        # Export data
        scraper.export_data(articles)

        print(f"\n✅ SUCCESS! Your MVP now has comprehensive spine industry content")
        print(f"🎯 Perfect for building content aggregation and analysis platforms!")

    else:
        print(f"\n❌ No articles were scraped")
        print(f"   Check browser setup and network connectivity")

if __name__ == "__main__":
    main()
