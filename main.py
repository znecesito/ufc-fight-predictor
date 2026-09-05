"""Entrypoint for the UFC Fight Predictor terminal app."""

import logging
import os

from dotenv import load_dotenv

from ufc_predictor.cli import run


def _configure_logging() -> None:
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("ufc_predictor.log")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger("ufc_predictor")
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


if __name__ == "__main__":
    load_dotenv()
    _configure_logging()
    run()
