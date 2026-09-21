import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect-public-boards.py"
spec = importlib.util.spec_from_file_location("public_boards", SCRIPT)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def job(title="Machine Learning Engineer", location="San Francisco, CA", content=None):
    return {
        "id": "test-job",
        "title": title,
        "location": {"name": location},
        "content": content or "Build and evaluate machine learning models for production inference.",
        "absolute_url": "https://example.com/jobs/test-job",
    }


class CollectionScreenTests(unittest.TestCase):
    def screen(self, raw):
        return collector.screen({"company": "Example", "board": "example"}, raw, set())

    def test_cambridge_uk_is_not_mapped_to_massachusetts(self):
        self.assertEqual(collector.locations("Cambridge, UK"), [])
        self.assertIsNone(self.screen(job(location="Cambridge, UK")))

    def test_ten_year_requirement_is_excluded_and_never_becomes_zero(self):
        self.assertIsNone(self.screen(job(content="Build machine learning systems. Requires 10 years of industry experience.")))

    def test_five_to_twelve_year_requirements_are_excluded(self):
        for years in (5, 8, 12):
            with self.subTest(years=years):
                self.assertIsNone(self.screen(job(content=f"Develop model inference systems with {years}+ years of experience.")))

    def test_ordinary_software_engineer_with_ai_boilerplate_is_excluded(self):
        raw = job(
            title="Software Engineer",
            content="Join our company. We work with AI and machine learning across the business. Build reliable web services.",
        )
        self.assertIsNone(self.screen(raw))

    def test_fellow_titles_are_excluded(self):
        self.assertIsNone(self.screen(job(title="AI Research Fellow")))

    def test_generic_remote_does_not_establish_us_location(self):
        self.assertEqual(collector.locations("Remote"), [])
        self.assertIsNone(self.screen(job(location="Remote")))

    def test_mixed_us_and_foreign_location_keeps_us_location(self):
        locations = collector.locations("London, UK; San Francisco, CA")
        self.assertEqual(locations, [{"city": "San Francisco", "state": "CA", "country": "US"}])
        result = self.screen(job(location="London, UK; San Francisco, CA"))
        self.assertIsNotNone(result)
        self.assertEqual(result["locations"], locations)

    def test_two_year_reference_remains_unclear_with_unknown_scalar_and_degree(self):
        result = self.screen(job(content="Build model inference services; 2 years of experience preferred."))
        self.assertIsNotNone(result)
        self.assertEqual(result["newgradStatus"], "unclear")
        path = result["qualificationPaths"][0]
        self.assertIsNone(path["minYears"])
        self.assertEqual(path["degrees"], [])
        self.assertEqual(result["experienceReferences"], [2])


if __name__ == "__main__":
    unittest.main()
