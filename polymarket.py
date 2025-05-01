import requests
import json
import re

class PolymarketMoves:
    @staticmethod
    def safe_parse_price(price_str):
        try:
            price_str = price_str.strip('[]"\'')
            return float(price_str)
        except (ValueError, TypeError):
            try:
                match = re.search(r'(\d+\.?\d*)', str(price_str))
                if match:
                    return float(match.group(1))
            except Exception:
                pass

            print(f"Warning: Could not parse price from {price_str}")
            return None


class PolymarketEventFetcher:
    def __init__(self):
        """Initialize the Polymarket event fetcher"""
        self.api_url = "https://gamma-api.polymarket.com/events"
        self.polymarket_moves = PolymarketMoves()

    def safe_parse_price(self, price_str):
        return PolymarketMoves.safe_parse_price(price_str)

    def get_market_events(self, include_closed=False):
        print("Fetching events from Polymarket...")
        try:
            r = requests.get(f"{self.api_url}?closed={str(include_closed).lower()}")
            r.raise_for_status()
            response = r.json()

            market_events = {}
            for event in response:
                market_events[event['id']] = event

            print(f"Found {len(market_events)} events on Polymarket")
            return market_events
        except Exception as e:
            print(f"Error retrieving Polymarket events: {e}")
            return {}

    def clean_text(self, text):
        return re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()

    # Search for markets
    def filter_events_by_keywords(self, events, keywords):
        filtered_events = {}
        cleaned_keywords = [self.clean_text(keyword) for keyword in keywords]

        for event_id, event in events.items():
            title = self.clean_text(event.get('title', ''))
            description = self.clean_text(event.get('description', ''))
            combined_text = f"{title} {description}"

            if any(kw in combined_text for kw in cleaned_keywords):
                filtered_events[event_id] = event

        return filtered_events



    # Show the markets
    def display_events(self, events):
        print("\n=== Market Events ===")
        event_ids = list(events.keys())
        for i, event_id in enumerate(event_ids, 1):
            event = events[event_id]
            print(f"{i}. {event.get('title', 'Untitled Event')}")
        return event_ids

    def display_event_markets(self, event):
        if 'markets' not in event:
            print("No markets found for this event.")
            return []

        print(f"\n=== Markets for {event.get('title', 'Event')} ===")
        markets = event['markets']

        for i, market in enumerate(markets, 1):
            print(f"{i}. {market.get('question', 'Unnamed Market')}")

            yes_price = None
            no_price = None
            # Show the probability
            try:
                if 'outcomePrices' in market:
                    prices = market['outcomePrices']

                    if isinstance(prices, str):
                        try:
                            prices = json.loads(prices)
                        except json.JSONDecodeError:
                            prices = [self.safe_parse_price(prices)]

                    if len(prices) >= 2:
                        yes_price = self.safe_parse_price(prices[0])
                        no_price = self.safe_parse_price(prices[1])

                    if yes_price is not None and no_price is not None:
                        print(f"   Yes Probability: {yes_price * 100:.2f}%")
                        print(f"   No Probability: {no_price * 100:.2f}%")
                    else:
                        print("   Prices not available")
                else:
                    print("   Prices not available")
            except Exception as e:
                print(f"   Error processing prices: {e}")

            if 'endDate' in market:
                print(f"   End Date: {market['endDate']}")

            print()

        return markets
