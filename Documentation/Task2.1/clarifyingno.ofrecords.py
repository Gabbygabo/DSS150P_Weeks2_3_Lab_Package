import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")  # adjust if your files live elsewhere

def count_json_records(filename):
    """Count records in a JSON file (list of objects)."""
    with open(DATA_DIR / filename, "r") as f:
        data = json.load(f)
    return len(data)

def count_parquet_records(filename):
    """Count records in a Parquet file using pandas."""
    df = pd.read_parquet(DATA_DIR / filename)
    return len(df)

if __name__ == "__main__":
    counts = {
        "api_events.json": count_json_records("api_events.json"),
        "orders.json": count_json_records("orders.json"),
        "products.parquet": count_parquet_records("products.parquet"),
        "products_optional_compare.json": count_json_records("products_optional_compare.json"),
    }
    print("Record counts per file:")
    for name, c in counts.items():
        print(f"  {name}: {c}")

