from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
import json

class BertSentimentAnalyzer:
    def __init__(self):
        self.model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        self.tokenizer = None
        self.model = None
        
    def load(self):
        """Load the BERT model and tokenizer"""
        print("Loading BERT model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        return self
    
    def predict(self, text):
        """Predict sentiment for given text"""
        if not self.model or not self.tokenizer:
            raise ValueError("Model not loaded. Call load() first.")
            
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
    
    def save_config(self, path="bert_config.json"):
        """Save model configuration"""
        config = {
            'model_name': self.model_name
        }
        with open(path, 'w') as f:
            json.dump(config, f)
            
    @classmethod
    def load_from_config(cls, path="bert_config.json"):
        """Load model from configuration"""
        analyzer = cls()
        analyzer.load()
        return analyzer