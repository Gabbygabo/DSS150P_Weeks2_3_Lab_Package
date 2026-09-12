from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, requests, uuid

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RAW = ROOT / 'raw'
STATE = ROOT / 'state'
API_URL = 'http://127.0.0.1:8000/api/events'

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def load_watermark():
    p = STATE / 'api_watermark.json'
    if not p.exists():
        return None
    return json.loads(p.read_text())['updated_at']

def save_watermark(value):
    STATE.mkdir(exist_ok=True)
    (STATE / 'api_watermark.json').write_text(json.dumps({'updated_at': value}, indent=2))

def log_run(run_id, start_ts, end_ts, status, source,
            records_read, records_written, duplicates_removed,
            watermark_before, watermark_after, error_message=""):
    log_path = ROOT / "templates" / "pipeline_run_log.csv"
    if not log_path.exists():
        header = ("run_id,start_ts,end_ts,status,source,"
                  "records_read,records_written,duplicates_removed,"
                  "watermark_before,watermark_after,error_message\n")
        log_path.write_text(header)

    row = (f"{run_id},{start_ts},{end_ts},{status},{source},"
           f"{records_read},{records_written},{duplicates_removed},"
           f"{watermark_before or ''},{watermark_after or ''},{error_message}\n")
    with log_path.open("a") as f:
        f.write(row)

def ingest_files():
    run_id = str(uuid.uuid4())
    start_ts = utc_now()
    status = "SUCCESS"
    error_message = ""
    records_read = 0
    records_written = 0
    duplicates_removed = 0

    try:
        RAW.mkdir(exist_ok=True)
        files_dir = RAW / 'files'
        files_dir.mkdir(exist_ok=True)

        manifest_path = files_dir / 'manifest.csv'
        existing_hashes = set()
        if manifest_path.exists():
            with manifest_path.open() as mf:
                for line in mf:
                    parts = line.strip().split(',')
                    if len(parts) == 4:
                        existing_hashes.add(parts[3])

        sources = ['customers.csv', 'orders.json', 'products.parquet']
        for fname in sources:
            src = DATA / fname
            if not src.exists():
                print(f"Missing source file: {fname}")
                continue

            records_read += 1
            file_hash = sha256_file(src)
            if file_hash in existing_hashes:
                duplicates_removed += 1
                print(f"Skipped duplicate {fname}")
                continue

            dst = files_dir / fname
            shutil.copy2(src, dst)
            size = src.stat().st_size
            ts = utc_now()
            with manifest_path.open('a') as mf:
                mf.write(f"{fname},{ts},{size},{file_hash}\n")
            records_written += 1
            print(f"Ingested {fname}")

    except Exception as e:
        status = "FAILURE"
        error_message = str(e)

    end_ts = utc_now()
    log_run(run_id, start_ts, end_ts, status, "files",
            records_read, records_written, duplicates_removed,
            None, None, error_message)

def fetch_api_page(page, per_page=20, updated_after=None):
    params = {'page': page, 'per_page': per_page}
    if updated_after:
        params['updated_after'] = updated_after
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def ingest_api():
    run_id = str(uuid.uuid4())
    start_ts = utc_now()
    status = "SUCCESS"
    error_message = ""
    records_read = 0
    records_written = 0
    duplicates_removed = 0
    watermark_before = load_watermark()
    watermark_after = None

    try:
        RAW.mkdir(exist_ok=True)
        api_dir = RAW / 'api'
        api_dir.mkdir(exist_ok=True)

        watermark = watermark_before
        page = 1
        all_records = {}
        latest_updated_at = watermark

        while True:
            try:
                data = fetch_api_page(page, per_page=20, updated_after=watermark)
            except requests.exceptions.RequestException as e:
                status = "FAILURE"
                error_message = str(e)
                break

            items = data.get("items", [])
            has_more = data.get("has_more", False)
            records_read += len(items)

            ts = utc_now()
            for rec in items:
                rec["_ingested_at"] = ts
                rec["_source"] = API_URL
                eid = rec["event_id"]
                if eid not in all_records:
                    all_records[eid] = rec
                    records_written += 1
                elif rec["updated_at"] > all_records[eid]["updated_at"]:
                    all_records[eid] = rec
                else:
                    duplicates_removed += 1

                if latest_updated_at is None or rec["updated_at"] > latest_updated_at:
                    latest_updated_at = rec["updated_at"]

            print(f"Ingested page {page} with {len(items)} records")

            if not has_more:
                break
            page += 1

        # Atomic write
        tmp_path = api_dir / 'events.jsonl.tmp'
        final_path = api_dir / 'events.jsonl'
        with tmp_path.open('w') as f:
            for rec in all_records.values():
                f.write(json.dumps(rec) + "\n")
        tmp_path.replace(final_path)

        if latest_updated_at:
            save_watermark(latest_updated_at)
            watermark_after = latest_updated_at
            print(f"Updated watermark to {latest_updated_at}")

    except Exception as e:
        status = "FAILURE"
        error_message = str(e)

    end_ts = utc_now()
    log_run(run_id, start_ts, end_ts, status, "api",
            records_read, records_written, duplicates_removed,
            watermark_before, watermark_after, error_message)

if __name__ == '__main__':
    RAW.mkdir(exist_ok=True)
    STATE.mkdir(exist_ok=True)
    ingest_files()
    ingest_api()
