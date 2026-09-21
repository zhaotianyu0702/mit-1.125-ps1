"""Regression: blank CSV cells must stay blank, not become an apostrophe."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('data_builder', Path(__file__).resolve().parents[1] / 'scripts/build-data.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class CsvExports(unittest.TestCase):
    def test_unknowns_zero_and_formula_safety(self):
        previous = builder.ROOT
        try:
            with tempfile.TemporaryDirectory() as directory:
                builder.ROOT = Path(directory)
                (builder.ROOT / 'dist/downloads').mkdir(parents=True)
                builder.write_csv('check.csv', [{'missing': None, 'empty': '', 'zero': 0, 'unsafe': '=1+1'}], ['missing', 'empty', 'zero', 'unsafe'])
                with (builder.ROOT / 'dist/downloads/check.csv').open(encoding='utf-8-sig', newline='') as stream:
                    row = next(csv.DictReader(stream))
                self.assertEqual(row, {'missing': '', 'empty': '', 'zero': '0', 'unsafe': "'=1+1"})
        finally:
            builder.ROOT = previous
