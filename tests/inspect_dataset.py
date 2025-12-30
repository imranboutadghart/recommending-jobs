from datasets import load_dataset

try:
    print("Loading dataset...")
    dataset = load_dataset("jacob-hugging-face/job-descriptions", split="train[:5]")
    print(f"Columns: {dataset.column_names}")
    for i, row in enumerate(dataset):
        print(f"\nRow {i}:")
        for col in dataset.column_names:
            val = str(row[col])[:100]
            print(f"  {col}: {val}...")
except Exception as e:
    print(f"Error: {e}")
