
# THIS IS IN PLACE NOW
import os
import requests
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

class TwitterSentimentAnalyzer:
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token
        
        # Call the BERT Sentiment Model
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
            response = requests.get(url, headers=headers, params=params)
            
            response.raise_for_status()
            
            data = response.json()
            
            tweets = data.get('data', [])
            
            return tweets
        
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving tweets: {e}")
            return []
    
    def analyze_sentiment(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = outputs.logits
            scores = torch.softmax(predictions, dim=1)
        
        scores = scores.numpy()[0]
        
        rating_mapping = {
            1: "very negative",
            2: "negative",
            3: "neutral",
            4: "positive",
            5: "very positive"
        }
        
        predicted_rating = np.argmax(scores) + 1
        sentiment = rating_mapping[predicted_rating]
        
        confidence = float(scores[predicted_rating - 1])
        
        return {
            'sentiment': sentiment,
            'confidence': round(confidence * 100, 2),
            'rating': predicted_rating,
            'raw_scores': {rating_mapping[i+1]: round(float(score) * 100, 2) 
                          for i, score in enumerate(scores)}
        }
    
    
    def analyze_tweets(self, query, max_results=10):
        tweets = self.get_tweets(query, max_results)
        
        # For each tweet
        analyzed_tweets = []
        for tweet in tweets:
            try:
                # Doing the actual entiment analysis
                sentiment = self.analyze_sentiment(tweet['text'])
                
                # Combine the two
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
    bearer_token = "AAAAAAAAAAAAAAAAAAAAAItNyQEAAAAAEJifeQ65OP4uzTGMQTl0MuUSzMQ%3DwfRK5Fpt6i1CjaqzhXKUn9qCHMSPZHOQ7GEnbx5zs65eeeIpZb"

    if not bearer_token:
        bearer_token = input("Enter your X (Twitter) Bearer Token: ")
    
    analyzer = TwitterSentimentAnalyzer(bearer_token)

    query = input("Enter search query: ")
    max_results = int(input("Enter max number of tweets to analyze (default 10): ") or 10)
    
    analyzed_tweets = analyzer.analyze_tweets(query, max_results)
    analyzer.print_results(analyzed_tweets)

if __name__ == "__main__":
    main()



