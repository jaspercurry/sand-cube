from __future__ import annotations

import copy
import unittest

from scripts.model_catalog import load_catalog, validate_catalog


class ModelCatalogTest(unittest.TestCase):
    def test_catalog_covers_the_repository(self) -> None:
        catalog = load_catalog()
        self.assertEqual(validate_catalog(catalog), [])
        self.assertGreaterEqual(len(catalog["models"]), 1)
        self.assertGreaterEqual(len(catalog["experiments"]), 1)

    def test_current_and_development_baselines_are_explicit(self) -> None:
        catalog = load_catalog()
        records = {model["id"]: model for model in catalog["models"]}

        current = records["final-enclosure-200"]
        self.assertEqual(current["status"], "stable")
        self.assertEqual(current["source"], "src/final_enclosure.py")

        development = records["development-190x210-tongue-groove"]
        self.assertEqual(development["status"], "development")
        self.assertEqual(
            development["source"],
            "src/enclosure_family/variant_r/model.py",
        )
        self.assertIn(
            "simple_tongue_groove_baffle",
            development["implementation"],
        )
        self.assertEqual(
            development["entrypoint"],
            "scripts/generate_variant_r.py",
        )

    def test_missing_experiment_record_is_a_failure(self) -> None:
        catalog = copy.deepcopy(load_catalog())
        removed = catalog["experiments"].pop()

        errors = validate_catalog(catalog)

        self.assertIn(
            f"uncataloged experiment directory: {removed['directory']}",
            errors,
        )
