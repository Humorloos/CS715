from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR.joinpath('data')
TARGET_DIR = PROJECT_DIR.joinpath('target')
LIFE_SCIENCES_TARGET_DIR = TARGET_DIR.joinpath('life_sciences')