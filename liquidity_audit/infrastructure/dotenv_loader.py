import pathlib

import dotenv

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_project_dotenv() -> None:
    dotenv.load_dotenv(_PROJECT_ROOT / ".env")
