# Content Curator Bot

An automated content curation system that aggregates news from multiple sources and shares them on X (Twitter) with proper attribution.

## Features

- Multi-source news aggregation (NewsAPI and NewsData.io)
- Automatic content formatting and sharing
- Rate limit handling
- Source attribution
- Docker support

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your API keys
3. Build and run using Docker

```bash
docker build -t content-curator .
docker run -d content-curator
```

## Environment Variables

Required environment variables in `.env`:

- `NEWS_API_KEY`: NewsAPI.org API key
- `NEWSDATA_API_KEY`: NewsData.io API key
- `TWITTER_API_KEY`: X/Twitter API key
- `TWITTER_API_SECRET`: X/Twitter API secret
- `TWITTER_BEARER_TOKEN`: X/Twitter bearer token
- `TWITTER_ACCESS_TOKEN`: X/Twitter access token
- `TWITTER_ACCESS_TOKEN_SECRET`: X/Twitter access token secret

## Usage

The bot will automatically:
- Fetch news articles from configured sources
- Format them according to X/Twitter requirements
- Share them with proper attribution
- Respect rate limits and platform policies

## Rate Limits

- NewsAPI: 100 requests/day (Developer plan)
- NewsData.io: Depends on plan
- X/Twitter: Follows v2 API rate limits

## Security Notes

- Never commit `.env` file to version control
- Regularly rotate API keys
- Monitor usage to stay within rate limits

## License

MIT License