# xTweets: AI-Powered Tech News Curator 🤖

An automated content curation system that fetches tech news articles and generates engaging tweets using Google's Gemini AI. Perfect for tech enthusiasts and news curators who want to maintain an active Twitter presence with high-quality, relevant content.

## Features

- 🔍 Automatic fetching of tech and science news articles
- 🧠 AI-powered tweet generation using Gemini 1.5
- 📊 Smart content caching system
- ⏱️ Rate limiting and error handling
- 📝 Comprehensive logging
- 🐳 Docker support for easy deployment

## How It Works

1. Fetches latest tech and science articles from The News API
2. Uses Google's Gemini AI to generate engaging tweet content
3. Automatically posts tweets with proper attribution and formatting
4. Maintains a cache of processed articles to avoid duplicates
5. Includes smart rate limiting to comply with API restrictions

## Requirements

- Python 3.9+
- Twitter API credentials
- The News API token
- Google Gemini API key

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/xtweets.git
cd xtweets
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
- Copy `.env.example` to `.env`
- Fill in your API credentials:
  - Twitter API credentials
  - The News API token
  - Gemini API key

## Configuration

The behavior can be customized through `config.py`:

- `MAX_TWEETS_PER_REQUEST`: Maximum tweets to post per run
- `CACHE_DURATION_HOURS`: How long to cache articles
- Various file paths for caching and logging

## Running the Application

### Direct Execution

```bash
python content_curator.py
```

### Using Docker

```bash
docker build -t xtweets .
docker run -d xtweets
```

## Features in Detail

### Smart Article Caching
- Prevents duplicate posts
- Reduces API calls
- Configurable cache duration

### AI Tweet Generation
- Ensures engaging content
- Includes emojis and hashtags
- Maintains proper attribution
- Smart length management

### Robust Error Handling
- Comprehensive logging
- Graceful failure recovery
- API rate limit management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Credit

Created by Anudeep - Feel free to reach out for questions or collaborations!