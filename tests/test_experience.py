import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "experience.py"
spec = importlib.util.spec_from_file_location("experience", SCRIPT)
experience = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experience)


class ExperienceClassificationTests(unittest.TestCase):
    def test_levels_are_title_based(self):
        self.assertEqual(experience.classify_experience("Machine Learning Engineer")["experienceLevel"], "unspecified")
        self.assertEqual(experience.classify_experience("Junior ML Engineer")["experienceLevel"], "entry")
        self.assertEqual(experience.classify_experience("Mid-Level ML Engineer")["experienceLevel"], "mid")
        self.assertEqual(experience.classify_experience("Staff ML Engineer")["experienceLevel"], "staff")
        self.assertEqual(experience.classify_experience("Director of ML")["experienceLevel"], "leadership")

    def test_senior_title_outranks_graduate_word(self):
        result = experience.classify_experience("Senior Engineer, New Graduate Programs")
        self.assertEqual(result["experienceLevel"], "senior")
        self.assertEqual(result["experienceLevelBasis"], "title")

    def test_member_of_technical_staff_is_not_staff_level(self):
        result = experience.classify_experience("Member of Technical Staff - New Grad")
        self.assertEqual(result["experienceLevel"], "new-grad")

    def test_business_lead_is_not_senior_level(self):
        result = experience.classify_experience("Machine Learning Engineer, Lead Ads")
        self.assertEqual(result["experienceLevel"], "unspecified")

    def test_curated_new_grad_fallback(self):
        result = experience.classify_experience("Machine Learning Engineer", "eligible")
        self.assertEqual(result["experienceLevel"], "new-grad")
        self.assertEqual(result["experienceLevelBasis"], "curated")

    def test_numeric_references_do_not_assign_level(self):
        result = experience.classify_experience("Engineer III", references=[10])
        self.assertEqual(result["experienceLevel"], "unspecified")
        self.assertEqual(result["experienceLevelBasis"], "unknown")


if __name__ == "__main__":
    unittest.main()
