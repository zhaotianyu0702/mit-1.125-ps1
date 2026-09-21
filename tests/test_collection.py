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

    def test_lowercase_nonstate_words_are_not_state_codes(self):
        self.assertEqual(collector.locations("Remote, in Europe"), [])
        self.assertEqual(collector.locations("Remote, or elsewhere"), [])

    def test_ten_year_requirement_is_retained_as_reference_and_never_becomes_zero(self):
        result = self.screen(job(content="Build machine learning systems. Requires 10 years of industry experience."))
        self.assertIsNotNone(result)
        self.assertEqual(result["experienceReferences"], [10])
        self.assertIsNone(result["qualificationPaths"][0]["minYears"])

    def test_five_to_twelve_range_is_retained_with_numeric_bounds(self):
        result = self.screen(job(content="Develop model inference systems with 5-12 years of experience."))
        self.assertIsNotNone(result)
        self.assertEqual(result["experienceReferences"], [5, 12])
        self.assertIsNone(result["qualificationPaths"][0]["minYears"])

    def test_word_number_experience_is_captured(self):
        result = self.screen(job(content="Develop model inference systems with ten years of experience."))
        self.assertIsNotNone(result)
        self.assertEqual(result["experienceReferences"], [10])

    def test_ordinary_software_engineer_with_ai_boilerplate_is_excluded(self):
        raw = job(
            title="Software Engineer",
            content="Join our company. We work with AI and machine learning across the business. Build reliable web services.",
        )
        self.assertIsNone(self.screen(raw))

    def test_nontechnical_fellow_titles_are_excluded(self):
        self.assertIsNone(self.screen(job(title="AI Research Fellow")))

    def test_senior_technical_title_is_retained(self):
        result = self.screen(job(title="Senior Machine Learning Engineer"))
        self.assertIsNotNone(result)
        self.assertEqual(result["experienceLevel"], "senior")

    def test_management_title_is_retained_when_technical(self):
        result = self.screen(job(title="Manager, Machine Learning Engineering"))
        self.assertIsNotNone(result)

    def test_business_ai_titles_are_excluded_even_with_technical_context(self):
        titles = [
            "Product Manager, Inference Platform",
            "Senior Manager, Technical Program Management (Search & AI)",
            "Partnership Manager, AI for Science",
            "Customer Success Manager, Managed Inference",
            "AI Success Manager",
            "Director, Product Marketing, AI",
            "Customer Enablement AI Programs",
            "AI Research Lab Strategy & Operations",
            "Head of Revenue Operations & AI",
            "Commodity Sourcing Manager, AI Infrastructure",
            "Strategic Partnerships, AI/API",
            "AI Journey Operations Manager",
            "Technical Account Manager, AI Infrastructure",
            "CX Strategy Manager, AI Transformation",
            "AI Strategist, Healthcare",
            "AI Deployment Strategist",
            "Strategic Finance Lead - AI",
            "Applied AI: Product Strategy & Revenue Lead",
            "Product Operations | AI Revenue Systems",
            "AI Strategy Consultant, Frontier Tech",
            "Accounting AI Solutions Lead",
            "Strategic AI Adoption Lead",
            "Staff Platform Manager, AI Personalization",
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertIsNone(self.screen(job(title=title)))

    def test_engineering_and_research_titles_with_business_context_are_retained(self):
        for title in (
            "AI Operations Engineer",
            "Software Engineer, AI Enablement",
            "Senior Machine Learning Engineer, Operations Research",
            "Data Scientist, Marketing",
            "Head of AI Enablement Engineering",
            "Finance & Strategy AI Engineer",
            "AI Engineer, Customer Success",
            "AI Operations Engineer, Partnerships",
            "Applied AI Architect, Partnerships",
            "Staff Software Engineer, GTM & AI Strategy",
        ):
            with self.subTest(title=title):
                self.assertIsNotNone(self.screen(job(title=title)))

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

    def test_go_language_requires_programming_context(self):
        for content in (
            "Build backend services in Go and Python.",
            "Experience with Golang and distributed systems.",
            "Strong programming skills in Go programming and Rust.",
            "Python, Go, and Rust are used in our model platform.",
        ):
            with self.subTest(content=content):
                result = self.screen(job(content="Build and evaluate machine learning models for production inference. " + content))
                self.assertIsNotNone(result)
                self.assertIn("Go", [skill["name"] for skill in result["skills"]])

    def test_go_prose_is_not_a_programming_skill(self):
        for content in (
            "Go beyond the usual expectations for machine learning systems.",
            "Partner with go-to-market teams on AI products.",
            "Go live with the new inference service.",
            "Experience with go-to-market teams.",
            "Python skills. Go beyond expectations.",
            "Python and Go-to-market experience.",
            "Strong Python skills help us Go beyond the baseline.",
            "Technologies: Python; go-to-market analytics.",
            "Experience with Go-to-market teams.",
        ):
            with self.subTest(content=content):
                result = self.screen(job(content="Build and evaluate machine learning models for production inference. " + content))
                self.assertIsNotNone(result)
                self.assertNotIn("Go", [skill["name"] for skill in result["skills"]])


if __name__ == "__main__":
    unittest.main()
