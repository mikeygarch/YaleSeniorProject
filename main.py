
# MONEYYYYY
#option.py
import os
import requests
import time
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import math

# Import from existing files in folder
from twitter_scraper import TwitterScraper
from twitter_analysis import TwitterSentimentAnalyzer
from polymarket import PolymarketEventFetcher

def get_search_query_from_market(event: Dict, market_index: int) -> Tuple[str, str]:
    if 'markets' not in event or market_index >= len(event['markets']):
        return event.get('title', ''), "event title"

    market = event['markets'][market_index]
    query = market.get('question', '')
    description = "market question"

    if not query:
        query = event.get('title', '')
        description = "event title"

    query = re.sub(r'[\"\'?\!]', '', query)
    query = re.sub(r'(\s+)', ' ', query)

    if len(query) > 100:
        query = query[:97] + "..."

    return query, description

class EnhancedTwitterSentimentAnalyzer(TwitterSentimentAnalyzer):
    def __init__(self, bearer_token):
        super().__init__(bearer_token)

    def print_results(self, analyzed_tweets, query):
        print(f"\n=== X SENTIMENT ANALYSIS RESULTS FOR: '{query}' ===")

        if not analyzed_tweets:
            print("No tweets found for this query.")
            return

        sentiment_counts = {"very negative": 0, "negative": 0, "neutral": 0, "positive": 0, "very positive": 0}
        total_rating = 0

        for tweet in analyzed_tweets:
            sentiment = tweet['sentiment_analysis']['sentiment']
            rating = tweet['sentiment_analysis']['rating']
            sentiment_counts[sentiment] += 1
            total_rating += rating

        print("\n--- INDIVIDUAL TWEETS ---")
        for i, tweet in enumerate(analyzed_tweets, 1):
            print(f"\n--- Tweet {i} ---")
            print(f"Author: @{tweet.get('author_username', 'unknown')}")
            print(f"Text: {tweet['text']}")
            print(f"Sentiment: {tweet['sentiment_analysis']['sentiment'].upper()}")
            print(f"Rating: {tweet['sentiment_analysis']['rating']}/5")
            print(f"Confidence: {tweet['sentiment_analysis']['confidence']}%")
            if 'public_metrics' in tweet and tweet['public_metrics']:
                metrics = tweet['public_metrics']
                print(f"Retweets: {metrics.get('retweet_count', 0)}")
                print(f"Likes: {metrics.get('like_count', 0)}")
                print(f"Replies: {metrics.get('reply_count', 0)}")
            print("---" * 10)

        print("\n--- SUMMARY ---")
        print(f"Total tweets analyzed: {len(analyzed_tweets)}")
        print(f"Average sentiment rating: {total_rating / len(analyzed_tweets):.2f}/5")
        print("Sentiment distribution:")
        for sentiment, count in sentiment_counts.items():
            percentage = (count / len(analyzed_tweets)) * 100
            print(f"  {sentiment.title()}: {count} tweets ({percentage:.1f}%)")

        average_rating = total_rating / len(analyzed_tweets)
        if average_rating > 3.5:
            print("\nOverall sentiment is POSITIVE")
        elif average_rating < 2.5:
            print("\nOverall sentiment is NEGATIVE")
        else:
            print("\nOverall sentiment is NEUTRAL")

def analyze_summary_vs_market(tweets: List[Dict[str, Any]]) -> Tuple[float, Dict[str, int]]:
    if not tweets:
        return 0.0, {}

    total_rating = 0
    sentiment_counts = {"very negative": 0, "negative": 0, "neutral": 0, "positive": 0, "very positive": 0}
    for tweet in tweets:
        sentiment = tweet['sentiment_analysis']['sentiment']
        rating = tweet['sentiment_analysis']['rating']
        sentiment_counts[sentiment] += 1
        total_rating += rating

    avg_rating = total_rating / len(tweets)
    return avg_rating, sentiment_counts

def extract_yes_probability(market: dict, price_parser) -> Optional[float]:
    try:
        if 'outcomePrices' in market:
            prices = market['outcomePrices']
            if isinstance(prices, str):
                try:
                    prices = json.loads(prices)
                except json.JSONDecodeError:
                    prices = [price_parser(prices)]
            if isinstance(prices, list) and len(prices) >= 1:
                return price_parser(prices[0])
    except Exception as e:
        print(f"Error extracting yes probability: {e}")
    return None

def calculate_market_rank_score(all_markets: List[dict], current_market: dict, price_parser) -> float:
    market_scores = []
    for m in all_markets:
        prob = extract_yes_probability(m, price_parser)
        if prob is not None:
            market_scores.append((m, prob))
    market_scores.sort(key=lambda x: x[1], reverse=True)

    total = len(market_scores)
    for i, (m, _) in enumerate(market_scores):
        if m == current_market:
            return 1 - (i / max(total - 1, 1))
    return 0.0

def main():
    api_keys = ["AAAAAAAAAAAAAAAAAAAAAItNyQEAAAAAEJifeQ65OP4uzTGMQTl0MuUSzMQ%3DwfRK5Fpt6i1CjaqzhXKUn9qCHMSPZHOQ7GEnbx5zs65eeeIpZb",
        os.environ.get("TWITTER_BEARER_TOKEN", ""),
        os.environ.get("X_API_KEY", ""), 
    ]

    api_keys_working = None
    print("=== Polymarket Twitter Sentiment Analyzer ===")

    for key in api_keys:
        if not key:
            continue
        try:
            analyzer = TwitterSentimentAnalyzer(key)
            api_keys_working = key
            break
        except Exception as e:
            print(f"API key setup failed: {e}")

    if not api_keys_working:
        api_keys_working = input("Enter your X (Twitter) Bearer Token: ")
        if not api_keys_working:
            print("No valid Twitter API key provided. Exiting.")
            return

    twitter_analyzer = EnhancedTwitterSentimentAnalyzer(api_keys_working)
    polymarket_fetcher = PolymarketEventFetcher()

    while True:
        try:
            keywords_input = input("Enter keywords to filter events (comma-separated, or type 'all' to show all markets, or press Enter for defaults): ")
            
            all_events = polymarket_fetcher.get_market_events()
            if not all_events:
                print("Could not retrieve events from Polymarket.")
                continue

            if keywords_input.strip().lower() == 'all':
                # Just pick the first 15 events
                filtered_events = dict(list(all_events.items())[:30])
                print(f"Showing {len(filtered_events)} markets without keyword filtering.")
            elif keywords_input.strip():
                keywords = [k.strip() for k in keywords_input.split(',')]
                filtered_events = polymarket_fetcher.filter_events_by_keywords(all_events, keywords)
                print(f"Filtered events found: {len(filtered_events)}")
                if not filtered_events:
                    print(f"No events found matching: {', '.join(keywords)}")
                    continue
            else:
                keywords = []
                filtered_events = polymarket_fetcher.filter_events_by_keywords(all_events, keywords)
                print(f"Filtered events found: {len(filtered_events)}")
                if not filtered_events:
                    print(f"No events found matching defaults.")
                    continue

            event_ids = polymarket_fetcher.display_events(filtered_events)
            event_choice = input("\nEnter the number of the event to analyze (0 to exit): ")

            if event_choice == '0':
                break

            event_choice = int(event_choice)
            if 1 <= event_choice <= len(event_ids):
                selected_event = filtered_events[event_ids[event_choice - 1]]
                markets = polymarket_fetcher.display_event_markets(selected_event)

                print("\nChoose Twitter analysis input:")
                print("1. Event title")
                print("2. Specific market question")
                search_choice = input("Enter your choice (1 or 2): ").strip()
                if search_choice not in {"1", "2"}:
                    print("Invalid input. Please enter 1 or 2.")
                    continue
                search_choice = int(search_choice)

                selected_market_index = 0

                if search_choice == 1:
                    query = selected_event.get('title', '')
                elif search_choice == 2 and markets:
                    market_num = int(input(f"Enter market number (1-{len(markets)}): "))
                    selected_market_index = market_num - 1
                    query, _ = get_search_query_from_market(selected_event, selected_market_index)
                else:
                    query = selected_event.get('title', '')

                print(f"Search query: '{query}'")
                if input("Modify this query? (y/n): ").lower() == 'y':
                    query = input("Enter modified search query: ")

                max_tweets = int(input("Enter max number of tweets (default 10): ") or 10)
                print(f"Fetching tweets for query: '{query}'...")
                tweets = twitter_analyzer.analyze_tweets(query, max_tweets)

                if not tweets:
                    print("No tweets found. Trying broader search...")
                    terms = re.findall(r'\b\w{4,}\b', query)
                    if terms:
                        broad_query = ' OR '.join(terms[:3])
                        print(f"Trying with broader query: '{broad_query}'")
                        tweets = twitter_analyzer.analyze_tweets(broad_query, max_tweets)
                        query = broad_query if tweets else query

                avg_rating, sentiment_counts = analyze_summary_vs_market(tweets)
                twitter_analyzer.print_results(tweets, query)

                market_to_compare = selected_event['markets'][selected_market_index] if selected_event.get('markets') else None
                polymarket_prob = extract_yes_probability(market_to_compare, polymarket_fetcher.safe_parse_price) if market_to_compare else None
                market_rank_score = calculate_market_rank_score(selected_event['markets'], market_to_compare, polymarket_fetcher.safe_parse_price)

                if polymarket_prob is not None:
                    sentiment_scaled = avg_rating / 5
                    print("\n=== COMPARISON TO POLYMARKET ===")
                    print(f"Market: {market_to_compare.get('question', 'Unknown Market')}")
                    print(f"Polymarket YES probability: {polymarket_prob*100:.2f}%")
                    print(f"Polymarket rank score (normalized): {market_rank_score:.2f}")
                    print(f"Average sentiment rating: {avg_rating:.2f}/5 ({sentiment_scaled*100:.2f}%)")
                    gap = sentiment_scaled - market_rank_score
                    print(f"Sentiment-Market Rank Difference: {gap:+.2f} (positive = sentiment is higher than market rank)")
                else:
                    print("\nPolymarket market probability could not be retrieved for comparison.")
            else:
                print("Invalid event number.")

        except Exception as e:
            print(f"Unexpected error: {e}")

        if input("Analyze another event? (y/n): ").lower() != 'y':
            break

if __name__ == "__main__":
    main()
