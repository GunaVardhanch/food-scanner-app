import torch
from transformers import BertTokenizerFast, BertForTokenClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
import json
import numpy as np

class FoodLabelDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def tokenize_and_align_labels(tokenizer, examples, tag2id):
    tokenized_inputs = tokenizer(
        examples["text"], 
        truncation=True, 
        is_split_into_words=False, 
        padding='max_length', 
        max_length=128
    )

    labels = []
    for i, label_list in enumerate(examples["labels"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                # Map the label to its ID. Note: simplified for this example
                # In real scenario, we'd need a more robust mapping between text tokens and labels
                label_ids.append(tag2id.get(label_list[word_idx % len(label_list)], 0))
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs

def train():
    # Load sample data
    with open('ner_sample_data.json', 'r') as f:
        data = json.load(f)
    
    texts = [item['text'] for item in data]
    tags = [item['labels'] for item in data]

    tag2id = {"O": 0, "B-CAL": 1, "I-CAL": 2, "B-SUGAR": 3, "I-SUGAR": 4, "B-ADD": 5, "I-ADD": 6}
    id2tag = {v: k for k, v in tag2id.items()}

    tokenizer = BertTokenizerFast.from_pretrained('bert-base-multilingual-cased')
    
    # Simple tokenization for the sample (is_split_into_words=False because sample text is a single string)
    encodings = tokenizer(texts, truncation=True, padding='max_length', max_length=128)
    
    # Manually creating label IDs for the sample (very simplified)
    label_ids = []
    for i in range(len(texts)):
        # Just a placeholder list of 0s, updated to -100 for padding
        l = [0] * 128
        label_ids.append(l)

    dataset = FoodLabelDataset(encodings, label_ids)

    model = BertForTokenClassification.from_pretrained(
        'bert-base-multilingual-cased', 
        num_labels=len(tag2id),
        id2label=id2tag,
        label2id=tag2id
    )

    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )

    print("Starting training...")
    # trainer.train() # Uncomment once libraries are ready
    print("Training component ready.")

if __name__ == "__main__":
    train()
