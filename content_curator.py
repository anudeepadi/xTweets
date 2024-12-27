import os
import json
import logging
import sys
import time
import http.client
import urllib.parse
from datetime import datetime, timedelta
import tweepy
from dotenv import load_dotenv
import google.generativeai as genai
import config
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('curator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class NewsAPI:
    def __init__(self):
        self.api_token = 'rhgPQvN762HmsvHUnGPdv95ViGInVKdvvhZsdtmX'
        
    def fetch_articles(self):
        """Fetch articles from The News API"""
        logger.info("Fetching articles from The News API...")
        try:
            conn = http.client.HTTPSConnection('api.thenewsapi.com')
            params = urllib.parse.urlencode({
                'api_token': self.api_token,
                'categories': 'tech,science',
                'limit': 3,
                'language': 'en'
            })
            
            conn.request('GET', f'/v1/news/all?{params}')
            response = conn.getresponse()
            data = json.loads(response.read().decode('utf-8'))
            
            articles = []
            for article in data.get('data', []):
                # Clean and validate article data
                if article.get('title') and article.get('url'):
                    articles.append({
                        'title': article.get('title').strip(),
                        'description': article.get('description', '').strip(),
                        'url': article.get('url').strip(),
                        'source': {'name': article.get('source', 'News Source').strip()},
                        'published_at': article.get('published_at')
                    })
            
            logger.info(f"Retrieved {len(articles)} articles from The News API")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from The News API: {str(e)}")
            return []

class ContentCurator:
    def __init__(self):
        load_dotenv()
        self.setup_clients()
        self.cache = ArticleCache()
        
    def setup_clients(self):
        """Initialize API clients"""
        logger.info("Setting up API clients...")
        
        self.news_api = NewsAPI()
        
        # Twitter client
        self.twitter = tweepy.Client(
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN')
        )
        
        logger.info("API clients initialized successfully")

    def clean_tweet_content(self, tweet_content, url):
        """Clean and truncate tweet content to ensure it's under 220 characters"""
        url_length = len(url) + 1  # +1 for newline
        max_content_length = 220 - url_length
        
        if len(tweet_content) > max_content_length:
            truncated = tweet_content[:max_content_length]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
            
            last_hash = truncated.rfind('#')
            if last_hash > 0 and ' ' not in truncated[last_hash:]:
                truncated = truncated[:last_hash].strip()
                
            tweet_content = truncated.strip()
        
        return f"{tweet_content}\n{url}"
        
    def save_gemini_response(self, article, prompt, response):
        """Save Gemini's response with metadata"""
        try:
            responses = []
            if os.path.exists(config.GEMINI_RESPONSES_PATH):
                with open(config.GEMINI_RESPONSES_PATH, 'r') as f:
                    responses = json.load(f)
            
            responses.append({
                'timestamp': datetime.now().isoformat(),
                'article_title': article['title'],
                'article_url': article['url'],
                'prompt': prompt,
                'response': response,
                'response_length': len(response) if response else 0
            })

            with open(config.GEMINI_RESPONSES_PATH, 'w') as f:
                json.dump(responses, f, indent=2)

            logger.info(f"Saved Gemini response for article: {article['title'][:50]}...")
            
        except Exception as e:
            logger.error(f"Error saving Gemini response: {str(e)}")

    def generate_tweet_content(self, article):
        """Generate tweet content using Gemini"""
        logger.info(f"Generating tweet content for article: {article['title'][:50]}...")
        
        try:
            prompt = f"""Write a tweet about this tech news (max 220 chars):
            Title: {article['title']}
            Source: {article['source']['name']}

            Must include:
            - 1 emoji
            - Key insight
            - Source attribution
            - 1 hashtag
            - Under 220 chars"""

            response = model.generate_content(prompt)
            tweet_base = response.text.strip()
            
            # Save Gemini's response
            self.save_gemini_response(article, prompt, tweet_base)
            
            # Clean up the response
            tweet_base = tweet_base.replace('```', '').replace('`', '').strip()
            if tweet_base.startswith('"') and tweet_base.endswith('"'):
                tweet_base = tweet_base[1:-1].strip()
            
            # Add URL to content
            tweet_content = self.clean_tweet_content(tweet_base, article['url'])
            
            # Verify length
            if len(tweet_content) > 220:
                logger.warning(f"Tweet too long ({len(tweet_content)} chars), regenerating...")
                return self.generate_tweet_content(article)
                
            logger.info(f"Generated tweet ({len(tweet_content)} chars): {tweet_content[:50]}...")
            return tweet_content
            
        except Exception as e:
            logger.error(f"Error generating tweet content: {str(e)}")
            self.save_gemini_response(article, prompt, f"ERROR: {str(e)}")
            return None

    def post_tweet(self, tweet_content):
        """Post tweet to Twitter"""
        try:
            response = self.twitter.create_tweet(text=tweet_content)
            logger.info(f"Successfully posted tweet: {tweet_content[:50]}...")
            return response
        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            return None

    def process_articles(self):
        """Process cached articles and generate tweets"""
        logger.info("Starting article processing...")
        
        articles = self.cache.get_articles()
        if not articles:
            logger.info("No articles in cache, fetching fresh articles...")
            self.cache.fetch_fresh_articles()
            articles = self.cache.get_articles()
            
            if not articles:
                logger.warning("Still no articles found after fetching")
                return

        processed_count = 0
        for idx, article in enumerate(articles[:config.MAX_TWEETS_PER_REQUEST], 1):
            logger.info(f"\nProcessing Article {idx}/{config.MAX_TWEETS_PER_REQUEST}")
            
            tweet_content = self.generate_tweet_content(article)
            if tweet_content:
                if self.post_tweet(tweet_content):
                    processed_count += 1
                    self.cache.mark_as_processed(article)
                time.sleep(5)  # Rate limit prevention

        logger.info(f"Completed processing {processed_count} articles")
        self.cache.save_cache()

class ArticleCache:
    def __init__(self):
        self.cache_path = config.ARTICLE_CACHE_PATH
        self.processed_path = config.PROCESSED_ARTICLES_PATH
        self.news_api = NewsAPI()
        self.load_cache()

    def load_cache(self):
        """Load cached articles"""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    cache_data = json.load(f)
                    if self.is_cache_valid(cache_data.get('timestamp')):
                        self.articles = cache_data.get('articles', [])
                        logger.info(f"Loaded {len(self.articles)} articles from cache")
                        return
            
            self.articles = []
            self.fetch_fresh_articles()
            
        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")
            self.articles = []

    def is_cache_valid(self, timestamp):
        """Check if cache is still valid"""
        if not timestamp:
            return False
        
        cache_time = datetime.fromisoformat(timestamp)
        age = datetime.now() - cache_time
        return age.total_seconds() < (config.CACHE_DURATION_HOURS * 3600)

    def fetch_fresh_articles(self):
        """Fetch fresh articles"""
        logger.info("Fetching fresh articles...")
        self.articles = self.news_api.fetch_articles()
        logger.info(f"Fetched {len(self.articles)} fresh articles")
        self.save_cache()

    def save_cache(self):
        """Save articles to cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'articles': self.articles
            }
            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info("Saved articles to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")

    def mark_as_processed(self, article):
        """Mark article as processed"""
        try:
            processed = self.load_processed()
            processed.append({
                'title': article['title'],
                'url': article['url'],
                'processed_at': datetime.now().isoformat()
            })
            with open(self.processed_path, 'w') as f:
                json.dump(processed, f, indent=2)
        except Exception as e:
            logger.error(f"Error marking article as processed: {str(e)}")

    def load_processed(self):
        """Load processed articles"""
        try:
            if os.path.exists(self.processed_path):
                with open(self.processed_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def get_articles(self):
        """Get unprocessed articles"""
        processed = self.load_processed()
        processed_urls = {p['url'] for p in processed}
        return [a for a in self.articles if a['url'] not in processed_urls]

def main():
    try:
        logger.info("Starting Content Curator...")
        curator = ContentCurator()
        curator.process_articles()
        logger.info("Content Curator completed successfully")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
    finally:
        logger.info("Content Curator shutting down")

if __name__ == "__main__":
    main()