
# THIS IS IN PLACE NOW
import os
import requests
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

class TwitterSentimentAnalyzer:
    def __init__(self, bearer_token):
        """
        Initialize Twitter Sentiment Analyzer
        
        Args:
            bearer_token (str): X API Bearer Token
        """
        self.bearer_token = bearer_token
        
        # Initialize BERT Sentiment Model
        self.model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
    
    def get_tweets(self, query, max_results=10):

        url = "https://api.twitter.com/2/tweets/search/recent"
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "SentimentAnalyzerV1"
        }
        
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "text,created_at,author_id,public_metrics"
        }
        
        try:
            # Make the API request
            response = requests.get(url, headers=headers, params=params)
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Extract tweets
            tweets = data.get('data', [])
            
            return tweets
        
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving tweets: {e}")
            return []
    
    def analyze_sentiment(self, text):
        """
        Predict sentiment for given text
        
        Args:
            text (str): Text to analyze
        
        Returns:
            dict: Sentiment analysis results
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = outputs.logits
            scores = torch.softmax(predictions, dim=1)
        
        # Convert scores to numpy for easier handling
        scores = scores.numpy()[0]
        
        # Map scores to sentiments
        rating_mapping = {
            1: "very negative",
            2: "negative",
            3: "neutral",
            4: "positive",
            5: "very positive"
        }
        
        predicted_rating = np.argmax(scores) + 1
        sentiment = rating_mapping[predicted_rating]
        
        # Calculate confidence
        confidence = float(scores[predicted_rating - 1])
        
        return {
            'sentiment': sentiment,
            'confidence': round(confidence * 100, 2),
            'rating': predicted_rating,
            'raw_scores': {rating_mapping[i+1]: round(float(score) * 100, 2) 
                          for i, score in enumerate(scores)}
        }
    
    def process_sentiment(sentiment: dict) -> str:
        data = {
    'sentiment': 'positive',
    'confidence': 87.45,
    'rating': 4,
    'raw_scores': {
        1: 3.21,
        2: 5.67,
        3: 12.35,
        4: 65.89,
        5: 12.88
    }
}
        raw_scores = sentiment['raw_scores']
        
    
    def analyze_tweets(self, query, max_results=10):
        """
        Retrieve and analyze tweets
        
        Args:
            query (str): Search term
            max_results (int): Maximum number of tweets to retrieve
        
        Returns:
            list: Analyzed tweets with sentiment
        """
        # Get tweets
        tweets = self.get_tweets(query, max_results)
        
        # Analyze sentiment for each tweet
        analyzed_tweets = []
        for tweet in tweets:
            try:
                # Perform sentiment analysis
                sentiment = self.analyze_sentiment(tweet['text'])
                
                # Combine tweet and sentiment data
                analyzed_tweet = {
                    **tweet,
                    'sentiment_analysis': sentiment
                }
                
                analyzed_tweets.append(analyzed_tweet)
                
            except Exception as e:
                print(f"Error analyzing tweet: {e}")
        
        return analyzed_tweets
    
    def print_results(self, analyzed_tweets):
        """
        Print sentiment analysis results
        
        Args:
            analyzed_tweets (list): List of analyzed tweets
        """
        print("\n=== X SENTIMENT ANALYSIS RESULTS ===")
        for tweet in analyzed_tweets:
            print("\n---Tweet---")
            print(f"Text: {tweet['text']}")
            print(f"Sentiment: {tweet['sentiment_analysis']['sentiment'].upper()}")
            print(f"Rating: {tweet['sentiment_analysis']['rating']}/5")
            print(f"Confidence: {tweet['sentiment_analysis']['confidence']}%")
            print("Detailed Scores:")
            for sent, score in tweet['sentiment_analysis']['raw_scores'].items():
                print(f"  {sent.title(): <15}: {score}%")
            print("---" * 10)

def main():
    # Get Bearer Token from environment or input
    bearer_token = "AAAAAAAAAAAAAAAAAAAAAItNyQEAAAAAEJifeQ65OP4uzTGMQTl0MuUSzMQ%3DwfRK5Fpt6i1CjaqzhXKUn9qCHMSPZHOQ7GEnbx5zs65eeeIpZb"

    if not bearer_token:
        bearer_token = input("Enter your X (Twitter) Bearer Token: ")
    
    # Create analyzer
    analyzer = TwitterSentimentAnalyzer(bearer_token)
    
    # Get search query
    query = input("Enter search query: ")
    max_results = int(input("Enter max number of tweets to analyze (default 10): ") or 10)
    
    # Analyze tweets
    analyzed_tweets = analyzer.analyze_tweets(query, max_results)
    
    # Print results
    analyzer.print_results(analyzed_tweets)

if __name__ == "__main__":
    main()



