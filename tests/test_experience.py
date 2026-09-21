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
    def test_four_level_taxonomy_and_twelve_diverse_examples(self):
        examples = {
            "New Grad ML Engineer": "entry", "Junior ML Engineer": "entry",
            "Machine Learning Engineer": "unspecified", "ML Engineer II": "unspecified",
            "Senior ML Engineer": "senior", "Mid-Level ML Engineer": "senior",
            "Principal Research Engineer": "staff", "Distinguished Scientist": "staff",
            "Engineering Manager, ML": "manager", "Director of ML": "manager",
            "Member of Technical Staff - New Grad": "entry",
            "Member of Technical Staff - Inference": "unspecified",
        }
        for title, expected in examples.items():
            self.assertEqual(experience.classify_experience(title)["experienceLevel"], expected, title)

    def test_manager_requires_actual_management_title(self):
        self.assertEqual(experience.classify_experience("Machine Learning Engineer, Lead Ads")["experienceLevel"], "unspecified")
        self.assertEqual(experience.classify_experience("Research Lead")["experienceLevel"], "senior")

    def test_title_and_curated_priority(self):
        self.assertEqual(experience.classify_experience("Senior ML Engineer", evidence={"required_years": 1})["experienceLevel"], "senior")
        result = experience.classify_experience("ML Engineer", "eligible", evidence={"required_years": 6})
        self.assertEqual((result["experienceLevel"], result["experienceLevelBasis"]), ("entry", "curated"))

    def test_numeric_requirements_use_broad_project_bucket(self):
        self.assertEqual(experience.classify_experience("ML Engineer", evidence={"required_years": 0})["experienceLevel"], "entry")
        result = experience.classify_experience("ML Engineer", evidence={"required_years": 3})
        self.assertEqual((result["experienceLevel"], result["requirementYears"]), ("senior", 3))
        self.assertEqual(experience.classify_experience("ML Engineer", evidence={"required_years": 10})["experienceLevel"], "senior")

    def test_scope_and_unknown(self):
        result = experience.classify_experience("ML Engineer", evidence={"scope_level": "staff", "scope_evidence": "Set technical strategy across multiple teams."})
        self.assertEqual((result["experienceLevel"], result["experienceLevelBasis"]), ("staff", "scope"))
        self.assertEqual(experience.classify_experience("ML Engineer", evidence={"open_level": "Levels vary by team."})["experienceLevel"], "unspecified")

    def test_extractor_ignores_preferred_and_company_history(self):
        evidence = enrich.extract_evidence("Founded in 2015 and serving customers for 10 years. Preferred: 5+ years of industry experience")
        self.assertEqual(evidence["evidenceType"], "none")

    def test_extractor_required_and_scope(self):
        evidence = enrich.extract_evidence("Required: 3+ years of relevant engineering experience.")
        self.assertEqual(evidence["required_years"], 3)
        self.assertIn("Required:", evidence["excerpt"])
        evidence = enrich.extract_evidence("You will own end-to-end production ML systems and drive technical decisions.")
        self.assertEqual(evidence["scope_level"], "senior")

    def test_degree_alternatives_same_bucket_are_usable(self):
        evidence = enrich.extract_evidence("Bachelor's degree and 2 years of experience, or Master's degree and 0 years of experience.")
        self.assertEqual(evidence["required_years"], 0)
        self.assertEqual(evidence["evidenceType"], "required-experience")

    def test_degree_alternatives_different_buckets_remain_ambiguous(self):
        evidence = enrich.extract_evidence("Bachelor's degree and 2 years of experience, or PhD and 5 years of experience.")
        self.assertNotIn("required_years", evidence)
        self.assertEqual(evidence["evidenceType"], "ambiguous-requirements")

    def test_protected_mts_and_phd_duration(self):
        self.assertEqual(experience.classify_experience("Member of Technical Staff - ML Research", evidence={"required_years": 5})["experienceLevel"], "senior")
        evidence = enrich.extract_evidence("PhD completed within 5 years; strong research background preferred.")
        self.assertEqual(evidence["evidenceType"], "none")

    def test_scope_overrides_generic_variable_level_boilerplate(self):
        evidence = enrich.extract_evidence("Years of experience will vary by level. You will define technical strategy across multiple teams.")
        result = experience.classify_experience("ML Engineer", evidence=evidence)
        self.assertEqual(result["experienceLevel"], "staff")

    def test_degree_can_substitute_for_experience(self):
        evidence = enrich.extract_evidence("Ph.D. in Computer Science or 2+ years of professional software engineering experience.")
        self.assertEqual(evidence["evidenceType"], "ambiguous-requirements")
        self.assertNotIn("required_years", evidence)

    def test_vague_or_company_prose_does_not_establish_seniority(self):
        for text in ["Prior experience with NLP is required.", "Have a track record of published research.", "Building on our track record of AI-powered solutions.", "Compensation considers prior relevant experience.", "Design and build production ML systems.", "For tech leadership roles, prior experience setting technical direction."]:
            result=experience.classify_experience("ML Engineer", evidence=enrich.extract_evidence(text))
            self.assertEqual(result["experienceLevel"], "unspecified", text)

    def test_years_shipping_and_multiple_required_floors(self):
        evidence=enrich.extract_evidence("Required qualifications\n6+ years of software engineering experience\n2+ years of machine learning experience")
        self.assertEqual(evidence["required_years"],6)
        evidence=enrich.extract_evidence("10+ years shipping production software")
        self.assertEqual(evidence["required_years"],10)

    def test_preferred_degree_and_location_do_not_hide_required_bullets(self):
        for text, years in [("San Francisco preferred.\nWhat we're looking for\n5+ years engineering experience",5),("Requirements\nBachelors degree; Masters preferred.\n2+ years of data science experience in industry",2)]:
            self.assertEqual(enrich.extract_evidence(text)["required_years"], years)

    def test_technical_or_is_not_alternative_experience_floor(self):
        result=enrich.extract_evidence("Qualifications\n6+ years of experience designing distributed systems or infrastructure in production\n2+ years of experience building ML infrastructure or systems in production")
        self.assertEqual(result["required_years"],6)

    def test_explicit_multi_level_range_stays_unspecified(self):
        for text in ["1–7 years of software engineering experience; hiring at multiple levels.","0–10 years of relevant experience"]:
            evidence=enrich.extract_evidence(text)
            self.assertEqual(evidence["evidenceType"],"ambiguous-requirements")
            self.assertNotIn("required_years",evidence)

if __name__ == "__main__":
    unittest.main()
