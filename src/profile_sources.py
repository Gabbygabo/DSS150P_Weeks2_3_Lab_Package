from pathlib import Path
import pandas as pd
import json

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'

def profile_csv(path):
    df = pd.read_csv(path)

    print(f"\n=== Profiling {path.name} ===")

    # File size
    size_bytes = path.stat().st_size
    print("File size (bytes):", size_bytes)

    # Row/column counts
    print("Shape (rows, cols):", df.shape)

    # Columns and inferred logical types
    print("\nColumn types:")
    print(df.dtypes)

    # Missing values by column
    print("\nMissing values per column:")
    print(df.isna().sum())

    # Exact duplicate rows
    print("\nDuplicate rows:", df.duplicated().sum())

    # Test uniqueness of customer_id
    if "customer_id" in df.columns:
        print("Is customer_id unique?:", df["customer_id"].is_unique)
    else:
        print("No customer_id column found.")

    # Candidate validation rules
    print("\nCandidate validation rules:")
    print("1. customer_id must be unique and non-null")
    print("2. email must contain '@' and a valid domain")
    print("3. signup_date must be a valid date not in the future")

def profile_json(path):
    print(f"\n=== Profiling {path.name} ===")

    with open(path, "r") as f:
        data = json.load(f)

    # Confirm root structure
    print("Root type:", type(data).__name__)
    if isinstance(data, list):
        print("Record count:", len(data))
        # Top-level keys
        keys = set().union(*(record.keys() for record in data))
        print("Top-level keys:", keys)

        # Identify nested field (e.g., shipping)
        nested_fields = [k for k in keys if isinstance(data[0].get(k), dict)]
        print("Nested fields:", nested_fields)

        # Identify timestamp and numeric fields
        sample = data[0]
        timestamp_fields = [k for k,v in sample.items() if isinstance(v, str) and ("date" in k or "time" in k)]
        numeric_fields = [k for k,v in sample.items() if isinstance(v, (int,float))]
        print("Timestamp fields:", timestamp_fields)
        print("Numeric fields:", numeric_fields)

        # Inspect nulls/missing keys
        null_counts = {k: sum(1 for rec in data if rec.get(k) in (None,"")) for k in keys}
        print("Nulls/missing per key:", null_counts)

        # Candidate downstream representations of nested shipping
        print("\nNested shipping object could be represented as:")
        print("1. Flattened into separate columns")
        print("2. Stored as a JSON column in a relational DB for flexibility")
    else:
        print("JSON root is not a list of records.")

def profile_parquet(path):
    print(f"\n=== Profiling {path.name} ===")

    df = pd.read_parquet(path, engine="pyarrow")

    # File size
    size_bytes = path.stat().st_size
    print("File size (bytes):", size_bytes)

    # Shape and dtypes
    print("Shape (rows, cols):", df.shape)
    print("\nColumn types:")
    print(df.dtypes)

    # Nulls
    print("\nMissing values per column:")
    print(df.isna().sum())

    # Compare schema behavior
    print("\nSchema behavior vs CSV/JSON:")
    print("- Parquet preserves column types (such as int64, datetime) more reliably.")
    print("- CSV infers everything as text unless parsed.")
    print("- JSON can mix types but is less strict.")

    # Optional comparison if same-data CSV/JSON exist
    csv_path = path.with_suffix(".csv")
    json_path = path.with_suffix(".json")
    if csv_path.exists():
        print(f"CSV size: {csv_path.stat().st_size} bytes")
    if json_path.exists():
        print(f"JSON size: {json_path.stat().st_size} bytes")
    print(f"Parquet size: {size_bytes} bytes")

    print("\nWhy Parquet is useful for analytics but not common operational source:")
    print("- Columnar storage is efficient for queries and compression.")
    print("- Operational systems often use row-oriented formats (CSV, JSON, relational tables) for easier transaction handling.")
    print("- Parquet is optimized for big data analytics, not day-to-day operational feeds.")

if __name__ == '__main__':
    profile_csv(DATA_DIR / 'customers.csv')
    profile_json(DATA_DIR / 'orders.json')
    profile_parquet(DATA_DIR / 'products.parquet')
