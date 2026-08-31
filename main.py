"""Entrypoint for the UFC Fight Predictor terminal app."""

from dotenv import load_dotenv

from ufc_predictor.cli import run

if __name__ == "__main__":
    load_dotenv()
    run()
