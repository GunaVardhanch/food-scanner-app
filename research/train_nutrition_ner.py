"""
Skeleton training script for a nutrition/ingredients NER model.

This script is intentionally minimal. It shows how you could fine-tune
`bert-base-multilingual-cased` (or similar) on token-level labels like:

    O, B-CAL, I-CAL, B-SUGAR, I-SUGAR, B-ADD, I-ADD, ...

The final model is saved under:
    D:\\food-scanner-models\\nutrition_ner\\

so that `NERService` in the backend automatically picks it up.
"""

import os
from pathlib import Path
from typing import List, Dict

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    BertTokenizerFast,
    BertForTokenClassification,
    AdamW,
    get_linear_schedule_with_warmup,
)

from app.config import NUTRITION_NER_MODEL_DIR


class NutritionNerDataset(Dataset):
    def __init__(
        self,
        texts: List[str],
        labels: List[List[int]],
        tokenizer: BertTokenizerFast,
        max_length: int = 128,
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        text = self.texts[idx]
        label_ids = self.labels[idx]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_offsets_mapping=True,
            return_tensors="pt",
        )

        # This example assumes label_ids is already aligned to tokens.
        # In a real implementation, you'd align char spans -> tokens here.
        labels_padded = [-100] * self.max_length
        for i in range(min(len(label_ids), self.max_length)):
            labels_padded[i] = label_ids[i]

        item = {k: v.squeeze(0) for k, v in encoding.items() if k != "offset_mapping"}
        item["labels"] = torch.tensor(labels_padded, dtype=torch.long)
        return item


def get_dummy_data(tag2id: Dict[str, int]):
    """
    Placeholder to keep this script runnable without a real dataset.
    Replace with your own loading logic from D:\\food-scanner-data.
    """
    texts = [
        "Nutrition Facts: Energy 525 kcal, Total Sugar 45.5g, Protein 6g.",
        "Per 100g: Energy 380 kcal, Sugar 12g, Fat 8g, Protein 5g.",
    ]
    # Very rough label examples (O = outside any entity)
    o = tag2id["O"]
    labels = [
        [o] * 10,
        [o] * 10,
    ]
    return texts, labels


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tag2id = {"O": 0, "B-CAL": 1, "I-CAL": 2, "B-SUGAR": 3, "I-SUGAR": 4, "B-ADD": 5, "I-ADD": 6}
    num_labels = len(tag2id)

    tokenizer = BertTokenizerFast.from_pretrained("bert-base-multilingual-cased")
    model = BertForTokenClassification.from_pretrained(
        "bert-base-multilingual-cased",
        num_labels=num_labels,
    ).to(device)

    texts, labels = get_dummy_data(tag2id)
    dataset = NutritionNerDataset(texts, labels, tokenizer)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    optimizer = AdamW(model.parameters(), lr=5e-5)
    num_epochs = 1
    num_training_steps = num_epochs * len(dataloader)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * num_training_steps),
        num_training_steps=num_training_steps,
    )

    model.train()
    for epoch in range(num_epochs):
        for batch in dataloader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

    # Save the fine-tuned model
    out_dir = Path(NUTRITION_NER_MODEL_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving NER model to {out_dir}")
    model.save_pretrained(out_dir)


if __name__ == "__main__":
    train()

