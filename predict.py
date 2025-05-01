import os
import sys
import logging
from typing import List, Dict

from twitter_scraper import TwitterScraper  # From the first file you provided
from model import BertSentimentAnalyzer  # From the BERT sentiment analysis file

class XSentimentAnalyzer:
    def __init__(self, bearer_token: str = None, verbose: bool = True):
        """
        Initialize X Sentiment Analysis pipeline
        
        Args:
            bearer_token (str, optional): X API Bearer Token
            verbose (bool, optional): Enable detailed logging
        """
        # Configure logging
        logging.basicConfig(
            level=logging.INFO if verbose else logging.WARNING,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        try:
            self.tweet_scraper = TwitterScraper(bearer_token, verbose)
            self.sentiment_analyzer = BertSentimentAnalyzer().load()
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
    
    def analyze_tweets(self, query: str, max_tweets: int = 10) -> List[Dict]:
        """
        Retrieve and analyze tweets for a given query
        
        Args:
            query (str): Search query for tweets
            max_tweets (int): Maximum number of tweets to retrieve and analyze
        
        Returns:
            List of tweet dictionaries with sentiment analysis
        """
        # Retrieve tweets
        tweets = self.tweet_scraper.get_tweets_with_retry(query, max_tweets)
        
        # Analyze sentiments
        analyzed_tweets = []
        for tweet in tweets:
            try:
                # Perform sentiment analysis on tweet text
                sentiment_result = self.sentiment_analyzer.predict(tweet['text'])
                
                # Combine tweet and sentiment data
                analyzed_tweet = {
                    **tweet,  # Original tweet metadata
                    'sentiment': {
                        'label': sentiment_result['sentiment'],
                        'rating': sentiment_result['rating'],
                        'confidence': sentiment_result['confidence'],
                        'detailed_scores': sentiment_result['raw_scores']
                    }
                }
                
                analyzed_tweets.append(analyzed_tweet)
                
            except Exception as e:
                self.logger.warning(f"Sentiment analysis failed for tweet: {e}")
        
        return analyzed_tweets
    
    def export_results(self, results: List[Dict], filename: str = 'x_sentiment_analysis.json'):
        """
        Export analysis results to a JSON file
        
        Args:
            results (List[Dict]): List of analyzed tweets
            filename (str): Output filename
        """
        try:
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Results exported to {filename}")
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
    
    def print_results(self, results: List[Dict]):
        """
        Print sentiment analysis results in a human-readable format
        
        Args:
            results (List[Dict]): List of analyzed tweets
        """
        print("\n=== X SENTIMENT ANALYSIS RESULTS ===")
        for tweet in results:
            print("\n---Tweet---")
            print(f"Text: {tweet['text']}")
            print(f"Author: {tweet.get('author_name', 'Unknown')}")
            print(f"Sentiment: {tweet['sentiment']['label'].upper()}")
            print(f"Rating: {tweet['sentiment']['rating']}/5")
            print(f"Confidence: {tweet['sentiment']['confidence']}%")
            print("Detailed Scores:")
            for sent, score in tweet['sentiment']['detailed_scores'].items():
                print(f"  {sent.title(): <15}: {score}%")
            print("---" * 10)

def main():
    # Configuration
    BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')  # Set in environment
    SEARCH_QUERY = input("Enter search query for tweets: ")
    MAX_TWEETS = int(input("How many tweets do you want to analyze? (default 10): ") or 10)
    
    try:
        # Initialize sentiment analyzer
        x_sentiment = XSentimentAnalyzer(BEARER_TOKEN)
        
        # Analyze tweets
        results = x_sentiment.analyze_tweets(SEARCH_QUERY, MAX_TWEETS)
        
        # Print results
        x_sentiment.print_results(results)
        
        # Optional: Export results
        export_choice = input("\nDo you want to export results to a JSON file? (y/n): ").lower()
        if export_choice == 'y':
            x_sentiment.export_results(results)
    
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()