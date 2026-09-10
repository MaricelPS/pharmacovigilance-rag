# src/ingest/download_faers.py
import requests
from pathlib import Path
import zipfile

QUARTERS = ["2024Q1", "2024Q2", "2024Q3", "2024Q4"]
BASE_URL = "https://fis.fda.gov/content/Exports/faers_ascii_{quarter}.zip"

def download_quarter(quarter: str, dest: Path):
    url = BASE_URL.format(quarter=quarter.lower())
    zip_path = dest / f"{quarter}.zip"
    # descarga con streaming
    r = requests.get(url, stream=True)
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest / quarter)