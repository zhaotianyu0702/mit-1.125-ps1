"""Broad, source-grounded experience buckets for the published job snapshot."""
import re


LEVELS = ("entry", "senior", "staff", "manager", "unspecified")


def classify_experience(title, newgrad_status="unclear", references=None, evidence=None):
    title = str(title or "").strip()
    lower = title.lower()
    # MTS is a company naming convention; Lead Ads/generation is a business
    # function. Neither should manufacture staff/senior seniority.
    lower = re.sub(r"\bmember of (?:the )?technical staff\b", "", lower)
    # Product and growth functions use Lead as a business descriptor.
    lower = re.sub(r"\blead (?:ads|generation)\b", "", lower)

    if re.search(r"\b(?:director|head|vp|vice president|chief|manager)\b", lower):
        return _result("manager", "title", "Title identifies a manager, director, head, VP, or chief role.")
    if re.search(r"\b(?:staff|principal|distinguished)\b", lower):
        return _result("staff", "title", "Title explicitly identifies staff, principal, or distinguished scope.")
    if re.search(r"\b(?:senior|sr\.?|lead|tech lead|team lead|mid[- ]level|intermediate)\b", lower):
        return _result("senior", "title", "Title identifies an experienced IC or lead-level role.")
    if re.search(r"\b(?:new\s+(?:college\s+)?grad(?:uate)?s?|graduate(?:s)?|junior|jr\.?|entry[- ]level|early[- ]career)\b", lower):
        return _result("entry", "title", "Title identifies a new-grad, junior, entry-level, or early-career role.")

    # Curated records may explicitly establish a new-grad pathway. Automated
    # discovery records intentionally remain unclear.
    if str(newgrad_status).lower() in {"explicit", "eligible", "confirmed", "new-grad", "newgrad", "yes"}:
        return _result("entry", "curated", "Curated record explicitly marks a new-grad pathway.")

    # Source evidence is deliberately considered only after explicit title and
    # curated signals.  The enrichment script supplies evidence extracted from
    # the requirements text; callers may also provide the same small schema.
    if evidence:
        scope_level = evidence.get("scope_level")
        if scope_level in {"staff", "manager", "senior"}:
            return _result(scope_level, "scope", evidence.get("scope_evidence") or evidence.get("open_level"))
        years = evidence.get("required_years")
        if isinstance(years, (int, float)) and not isinstance(years, bool):
            years = int(years)
            if years <= 2:
                return _result("entry", "requirements", evidence.get("evidence") or f"Requirements state at least {years} years of relevant experience.", years)
            return _result("senior", "requirements", evidence.get("evidence") or f"Requirements state at least {years} years of relevant experience; the project groups 3+ years as senior.", years)

    # Engineer II/III and numeric references alone are deliberately ambiguous.
    return _result("unspecified", "unknown", (evidence or {}).get("reason") or "No unambiguous experience level appears in the title or requirements.")


def _result(level, basis, evidence, requirement_years=None):
    result = {"experienceLevel": level, "experienceLevelBasis": basis, "experienceLevelEvidence": evidence}
    if requirement_years is not None:
        result["requirementYears"] = requirement_years
    return result
