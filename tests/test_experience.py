import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "experience.py"
spec = importlib.util.spec_from_file_location("experience", SCRIPT)
experience = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experience)
enrich_spec = importlib.util.spec_from_file_location("enrich_experience", SCRIPT.parent / "enrich-experience.py")
enrich = importlib.util.module_from_spec(enrich_spec)
enrich_spec.loader.exec_module(enrich)


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

    def test_required_years_are_the_fallback_signal(self):
        result = experience.classify_experience("Machine Learning Engineer", evidence={"required_years": 2, "evidence": "At least 2 years of relevant experience."})
        self.assertEqual(result["experienceLevel"], "entry")
        self.assertEqual(result["experienceLevelBasis"], "requirements")
        self.assertEqual(result["requirementYears"], 2)
        self.assertEqual(experience.classify_experience("Machine Learning Engineer", evidence={"required_years": 4})["experienceLevel"], "mid")
        self.assertEqual(experience.classify_experience("Machine Learning Engineer", evidence={"required_years": 5})["experienceLevel"], "senior")

    def test_preferred_years_are_not_a_required_fallback(self):
        result = experience.classify_experience("Machine Learning Engineer", evidence={"preferred_years": 5})
        self.assertEqual(result["experienceLevel"], "unspecified")

    def test_explicit_scope_and_experience_without_years(self):
        result = experience.classify_experience("Machine Learning Engineer", evidence={"open_level": "Open to candidates at multiple levels."})
        self.assertEqual((result["experienceLevel"], result["experienceLevelBasis"]), ("open-level", "scope"))
        result = experience.classify_experience("Machine Learning Engineer", evidence={"experienced": "Demonstrated professional experience is required."})
        self.assertEqual((result["experienceLevel"], result["experienceLevelBasis"]), ("experienced", "requirements"))

    def test_title_and_curated_override_source_evidence(self):
        self.assertEqual(experience.classify_experience("Senior ML Engineer", evidence={"required_years": 1})["experienceLevel"], "senior")
        self.assertEqual(experience.classify_experience("ML Engineer", "eligible", evidence={"required_years": 6})["experienceLevel"], "new-grad")

    def test_mts_title_keeps_new_grad_override(self):
        result = experience.classify_experience("Member of Technical Staff - New Grad", evidence={"required_years": 5})
        self.assertEqual(result["experienceLevel"], "new-grad")

    def test_extractor_distinguishes_required_preferred_and_unrelated_years(self):
        evidence = enrich.extract_evidence("Founded in 2015 and serving customers for 10 years. Required: 3+ years of relevant engineering experience.")
        self.assertEqual(evidence["required_years"], 3)
        self.assertIn("Required:", evidence["excerpt"])
        evidence = enrich.extract_evidence("Preferred qualifications:\n5+ years of industry experience")
        self.assertEqual(evidence["evidenceType"], "none")

    def test_extractor_excludes_team_history_and_mentoring_scope(self):
        evidence = enrich.extract_evidence("Our team has 20 years of professional engineering experience. Mentor junior engineers and partner with senior staff.")
        self.assertEqual(evidence["evidenceType"], "none")

    def test_extractor_marks_variable_internal_levels_as_scope(self):
        evidence = enrich.extract_evidence("Years of experience required will correlate with the internal job level requirements.")
        self.assertEqual(evidence["evidenceType"], "scope")

    def test_extractor_does_not_choose_degree_alternative_minimum(self):
        evidence = enrich.extract_evidence("Bachelor's degree and 2 years of experience, or Master's degree and 0 years of experience.")
        self.assertNotIn("required_years", evidence)
        self.assertEqual(evidence["evidenceType"], "none")

    def test_abbreviated_degrees_still_make_alternatives_ambiguous(self):
        evidence = enrich.extract_evidence("New grad Ph.D in ML/AI or 2+ years of industry experience in applied ML/AI with a M.S.")
        self.assertNotIn("required_years", evidence)
        self.assertNotIn("experienced", evidence)

    def test_concrete_years_outrank_generic_level_boilerplate(self):
        evidence = enrich.extract_evidence("Required: 4+ years of relevant engineering experience.\nYears of experience required will correlate with internal job level requirements.")
        self.assertEqual(evidence["required_years"], 4)

    def test_extractor_marks_explicit_open_level_scope(self):
        evidence = enrich.extract_evidence("We are open to candidates at multiple seniority levels, from junior to senior.")
        self.assertEqual(evidence["evidenceType"], "scope")


if __name__ == "__main__":
    unittest.main()
