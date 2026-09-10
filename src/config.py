"""Central configuration loader for the pharmacovigilance project."""
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REFERENCE_DIR = DATA_DIR / "reference"

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

# Project scope: GLP-1 receptor agonists
THERAPEUTIC_CLASS = os.getenv("THERAPEUTIC_CLASS", "GLP-1")
TARGET_DRUGS = os.getenv("TARGET_DRUGS", "").split(",")
FAERS_QUARTERS = os.getenv("FAERS_QUARTERS", "").split(",")

# Ensure directories exist
for directory in [RAW_DIR, PROCESSED_DIR, REFERENCE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)