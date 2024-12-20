from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

# API Keys
NEWS_API_KEY = "f72afb2d36394ef5b06845ec7baa6260"
STOCKS_API_KEY = "SZJO1JZ4EV7EBOC0"

# Base URLs
NEWS_API_URL = "https://newsapi.org/v2/everything"
STOCKS_API_URL = "https://www.alphavantage.co/query"


@app.get("/search/{input_value}")
def search(input_value: str):
    """
    Fetch news articles, current stock price, historical stock data, and provide an investment suggestion.
    Handle both company symbols and company names.
    """
    try:
        # Convert company name to stock symbol if necessary
        if not is_symbol(input_value):
            stock_symbol = get_symbol_from_name(input_value)
            if not stock_symbol:
                raise HTTPException(status_code=404, detail="Stock symbol not found for the given company name")
        else:
            stock_symbol = input_value

        # Fetch stock data
        stock_data = get_stock_data(stock_symbol)
        if not stock_data:
            raise HTTPException(status_code=404, detail="Stock data not found")

        current_price = stock_data["current_price"]
        historical_data = stock_data["historical_data"]

        # Fetch news articles
        news = get_news(stock_symbol)
        if not news:
            raise HTTPException(status_code=404, detail="News articles not found")

        # Analyze the historical data and news for investment suggestion
        suggestion, summary = analyze_investment(historical_data, current_price, news)

        # Display only for debugging in the terminal (optional)
        print(f"\n--- Analysis for {input_value} ({stock_symbol}) ---")
        print(f"Current Price: ${current_price}")
        print("\nTop News Articles:")
        for article in news:
            print(f"- {article['title']} ({article['url']})")
        print(f"\nInvestment Suggestion: {suggestion}")
        print(f"Summary: {summary}")

        # Return results for API response
        return {
            "input": input_value,
            "stock_symbol": stock_symbol,
            "current_price": current_price,
            "historical_data": historical_data,
            "news": news,
            "suggestion": suggestion,
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def is_symbol(input_value: str) -> bool:
    """
    Determine if the input is likely a stock symbol (short and uppercase).
    """
    return len(input_value) <= 5 and input_value.isupper()


def get_symbol_from_name(company_name: str) -> str:
    """
    Convert a company name to its stock symbol using the Alpha Vantage API.
    """
    try:
        response = requests.get(
            STOCKS_API_URL,
            params={
                "function": "SYMBOL_SEARCH",
                "keywords": company_name,
                "apikey": STOCKS_API_KEY
            }
        )
        if response.status_code != 200:
            raise Exception("Failed to fetch stock symbol")

        data = response.json().get("bestMatches", [])
        if not data:
            return None

        # Return the most relevant symbol
        return data[0]["1. symbol"]  # The key for the symbol in the API response
    except Exception as e:
        print(f"Error fetching stock symbol: {e}")
        return None


def get_stock_data(symbol: str):
    """
    Fetch stock data including current price and historical data from the Stocks API.
    """
    # Fetch current stock price
    current_price_response = requests.get(
        STOCKS_API_URL,
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": STOCKS_API_KEY
        }
    )
    if current_price_response.status_code != 200:
        return None

    current_price_data = current_price_response.json()
    try:
        current_price = float(current_price_data["Global Quote"]["05. price"])
    except KeyError:
        return None

    # Fetch historical stock data (5 years)
    historical_response = requests.get(
        STOCKS_API_URL,
        params={
            "function": "TIME_SERIES_MONTHLY_ADJUSTED",
            "symbol": symbol,
            "apikey": STOCKS_API_KEY
        }
    )
    if historical_response.status_code != 200:
        return None

    historical_data = historical_response.json().get("Monthly Adjusted Time Series", {})

    # Process the historical data for the past 5 years
    processed_data = []
    for date, data in historical_data.items():
        processed_data.append({"date": date, "price": float(data["4. close"])})

    # Limit to the most recent 60 months (5 years)
    processed_data = processed_data[:60]

    return {"current_price": current_price, "historical_data": processed_data}


def get_news(query: str):
    """
    Fetch top 5 news articles about the company or symbol using the News API.
    """
    response = requests.get(
        NEWS_API_URL,
        params={
            "q": query,
            "apiKey": NEWS_API_KEY,
            "pageSize": 5,
            "sortBy": "relevance"
        }
    )
    if response.status_code != 200:
        return None

    articles = response.json().get("articles", [])
    news_data = [
        {"title": article["title"], "url": article["url"]}
        for article in articles
    ]
    return news_data


def analyze_investment(historical_data, current_price, news):
    """
    Analyze stock trends and news sentiment to provide an investment suggestion and a summary.
    """
    # Analyze historical data (growth trend)
    prices = [entry["price"] for entry in historical_data]
    growth_rate = (prices[-1] - prices[0]) / prices[0] * 100

    # Simple analysis logic
    if growth_rate > 20 and len(news) >= 3:
        suggestion = "Invest"
        summary = (
            f"The stock has shown a strong growth rate of {growth_rate:.2f}% over the past 5 years, "
            f"and recent news sentiment is predominantly positive. This indicates good potential for investment."
        )
    elif growth_rate > 0:
        suggestion = "Hold"
        summary = (
            f"The stock has grown by {growth_rate:.2f}% over the past 5 years. However, mixed or neutral news sentiment "
            f"suggests that it may be better to wait before making a decision."
        )
    else:
        suggestion = "Avoid"
        summary = (
            f"The stock has declined by {growth_rate:.2f}% over the past 5 years, and recent news sentiment is not "
            f"favorable. Investing in this stock may carry significant risk."
        )

    return suggestion, summary


if __name__ == "__main__":
    # Simple CLI for testing
    user_input = input("Enter a company symbol or name (e.g., TSLA or Tesla): ").strip()
    response = search(user_input)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from the React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
