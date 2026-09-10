"""Download FAERS quarterly ASCII data from the FDA public portal."""
from pathlib import Path
from typing import Iterable
import zipfile

import requests
from tqdm import tqdm

from src.config import RAW_DIR, FAERS_QUARTERS

BASE_URL = "https://fis.fda.gov/content/Exports/faers_ascii_{quarter}.zip"


def download_quarter(quarter: str, dest_dir: Path) -> Path:
    """Download and extract a single FAERS quarter.

    Args:
        quarter: Quarter identifier, e.g. '2024Q1'.
        dest_dir: Directory where the ZIP will be saved and extracted.

    Returns:
        Path to the extracted quarter folder.
    """
    quarter_lower = quarter.lower()  # FDA URLs use lowercase (e.g. 2024q1)
    url = BASE_URL.format(quarter=quarter_lower)
    zip_path = dest_dir / f"{quarter}.zip"
    extract_path = dest_dir / quarter

    if extract_path.exists() and any(extract_path.rglob("*.txt")):
        print(f"[skip] {quarter} already extracted at {extract_path}")
        return extract_path

    print(f"[download] {quarter} from {url}")
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))

    with open(zip_path, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=quarter
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

    print(f"[extract] {quarter} -> {extract_path}")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(extract_path)

    # Remove ZIP to save disk space (uncomment if desired)
    # zip_path.unlink()

    return extract_path


def download_all(quarters: Iterable[str], dest_dir: Path) -> list[Path]:
    """Download all requested quarters."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    return [download_quarter(q, dest_dir) for q in quarters]


if __name__ == "__main__":
    print(f"Target quarters: {FAERS_QUARTERS}")
    print(f"Destination: {RAW_DIR}")
    paths = download_all(FAERS_QUARTERS, RAW_DIR)
    print("\nDone. Extracted folders:")
    for p in paths:
        print(f"  - {p}")