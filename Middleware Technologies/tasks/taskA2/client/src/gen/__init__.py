# Hack when running as `python -m src.client.StockAlerterClient`
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
