from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from datasets import Dataset
import torch
import numpy as np
from sklearn.model_selection import train_test_split
import pandas as pd

def prepare_training_data():
    """
    Prepare sample training data. In real use, you might load this from a file
    or database containing labeled tweets.
    """
    training_data = {
        'text': [
            "This game was absolutely amazing! Best Super Bowl ever! 🏈",
            "Terrible performance today, what a disappointment 😤",
            "Not bad, but could have been better. Decent game overall.",
            # Add more examples...
        ],
        'label': [
            2,  # Very positive (0=very negative, 1=negative, 2=neutral, 3=positive, 4=very positive)
            0,  # Very negative
            1,  # Neutral
        ]
    }
    return pd.DataFrame(training_data)

def train_model():
    # Load pre-trained model and tokenizer
    model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    # Prepare data
    df = prepare_training_data()
    train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42)
    
    # Convert to Hugging Face datasets
    def convert_to_dataset(dataframe):
        return Dataset.from_dict({
            'text': dataframe['text'].tolist(),
            'label': dataframe['label'].tolist()
        })
    
    train_dataset = convert_to_dataset(train_df)
    eval_dataset = convert_to_dataset(eval_df)
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
    )
    
    # Define trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )
    
    # Train the model
    trainer.train()
    
    # Save the trained model
    model.save_pretrained("./trained_model")
    tokenizer.save_pretrained("./trained_model")

if __name__ == "__main__":
    train_model()