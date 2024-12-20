import requests
from textblob import TextBlob

# API Key and Endpoint for News
NEWS_API_KEY = "f72afb2d36394ef5b06845ec7baa6260"
NEWS_API_URL = "https://newsapi.org/v2/everything"

def fetch_market_news():
    """
    Fetch recent news articles related to overall stock market growth.
    """
    response = requests.get(
        NEWS_API_URL,
        params={
            "q": "stock market growth",
            "sortBy": "relevance",
            "language": "en",
            "apiKey": NEWS_API_KEY,
            "pageSize": 5  # Fetch top 5 articles
        }
    )
    
    if response.status_code != 200:
        raise Exception("Failed to fetch market news")
    
    news_data = response.json().get("articles", [])
    return [{"title": article["title"], "description": article["description"], "url": article["url"]} for article in news_data]


def analyze_news_sentiment(news_articles):
    """
    Analyze sentiment of the fetched news articles and generate a summary.
    """
    positive_count = 0
    neutral_count = 0
    negative_count = 0
    sentiment_summary = []

    for article in news_articles:
        # Use TextBlob for sentiment analysis
        description = article.get("description", "")
        if description:
            sentiment = TextBlob(description).sentiment.polarity
            if sentiment > 0:
                positive_count += 1
                sentiment_summary.append(f"Positive: {article['title']}")
            elif sentiment == 0:
                neutral_count += 1
                sentiment_summary.append(f"Neutral: {article['title']}")
            else:
                negative_count += 1
                sentiment_summary.append(f"Negative: {article['title']}")
    
    # Generate summary based on sentiment counts
    if positive_count > negative_count:
        overall_summary = "The overall sentiment around the stock market growth is positive. This may indicate a favorable investment climate."
    elif negative_count > positive_count:
        overall_summary = "The overall sentiment around the stock market growth is negative. Caution is advised before making investment decisions."
    else:
        overall_summary = "The overall sentiment around the stock market growth is neutral. Market conditions may be stable but uncertain."

    return overall_summary, sentiment_summary


def display_market_trends():
    """
    Fetch market news, analyze sentiment, and display results.
    """
    try:
        # Fetch news articles
        news_articles = fetch_market_news()

        # Analyze sentiment and generate summary
        overall_summary, sentiment_summary = analyze_news_sentiment(news_articles)

        # Display results
        print("\n--- Market News Articles ---")
        for article in news_articles:
            print(f"- {article['title']} ({article['url']})")

        print("\n--- Sentiment Analysis Summary ---")
        for summary in sentiment_summary:
            print(f"- {summary}")

        print("\n--- Overall Summary ---")
        print(overall_summary)

        # Return the data for use in a web page
        return {
            "news_articles": news_articles,
            "overall_summary": overall_summary,
            "sentiment_summary": sentiment_summary
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}


# Run this to test the functionality (can be removed for integration)
if __name__ == "__main__":
    display_market_trends()
