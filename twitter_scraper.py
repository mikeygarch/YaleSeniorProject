

# attempt

import os
import requests
import time
import logging
from typing import List, Dict, Optional

class TwitterScraper:
    def __init__(self, bearer_token: Optional[str] = None, verbose: bool = False):
        logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        
        self.logger = logging.getLogger(__name__)
        self.bearer_token = "AAAAAAAAAAAAAAAAAAAAAItNyQEAAAAAEJifeQ65OP4uzTGMQTl0MuUSzMQ%3DwfRK5Fpt6i1CjaqzhXKUn9qCHMSPZHOQ7GEnbx5zs65eeeIpZb"
        
        if not self.bearer_token:
            raise ValueError("Twitter Bearer Token is required. Set TWITTER_BEARER_TOKEN environment variable.")
        
        self._validate_token()

    def _validate_token(self):
 
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        
        try:
            response = requests.get(url, headers=headers, params={"query": "test", "max_results": 1})
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Token validation failed: {e}")
            raise ValueError("Invalid Twitter Bearer Token")
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Network error during token validation: {e}")

    def get_tweets_with_retry(self, query: str, max_results: int = 10, max_retries: int = 3) -> List[Dict]:

        for attempt in range(max_retries):
            try:
                tweets = self._search_tweets(query, max_results)
                
                if tweets:
                    return tweets
                
                self.logger.info(f"No tweets found. Attempt {attempt + 1} of {max_retries}")
                
                time.sleep(2 ** attempt)
            
            except Exception as e:
                self.logger.error(f"Error in attempt {attempt + 1}: {e}")
                
                time.sleep(2 ** attempt)
        
        self.logger.error("Failed to retrieve tweets after multiple attempts.")
        return []

    def _search_tweets(self, query: str, max_results: int = 10) -> List[Dict]:
        url = "https://api.twitter.com/2/tweets/search/recent"
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}"
        }
        
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,author_id,public_metrics,text",
            "expansions": "author_id",
            "user.fields": "name,username,profile_image_url"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return self._process_tweets(data)
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP Error: {e}")
            error_map = {
                401: "Authentication error. Check your bearer token.",
                429: "Rate limit exceeded. Try again later.",
                403: "Forbidden. Check your API permissions."
            }
            self.logger.error(error_map.get(response.status_code, "Unexpected HTTP error"))
            self.logger.error(f"Response text: {response.text}")
            return []
        except requests.exceptions.ConnectionError:
            self.logger.error("Network connection error")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []

    def _process_tweets(self, data: Dict) -> List[Dict]:

        processed_tweets = []
        
        if "data" not in data:
            self.logger.info("No tweets found in the response")
            return processed_tweets
        
        users = {}
        if "includes" in data and "users" in data["includes"]:
            for user in data["includes"]["users"]:
                users[user["id"]] = user
        
        for tweet in data["data"]:
            author_id = tweet.get("author_id")
            author = users.get(author_id, {})
            
            processed_tweet = {
                "id": tweet.get("id"),
                "text": tweet.get("text"),
                "created_at": tweet.get("created_at"),
                "author_name": author.get("name"),
                "author_username": author.get("username"),
                "public_metrics": {
                    "retweet_count": tweet.get("public_metrics", {}).get("retweet_count", 0),
                    "like_count": tweet.get("public_metrics", {}).get("like_count", 0),
                    "reply_count": tweet.get("public_metrics", {}).get("reply_count", 0)
                }
            }
            
            processed_tweets.append(processed_tweet)
        
        return processed_tweets
    









