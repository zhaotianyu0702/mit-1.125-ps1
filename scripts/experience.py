"""Conservative title-based experience-level classification for discovery roles.

Numeric years mentioned in a posting are evidence only. They never determine the
title level because postings frequently mix preferred qualifications, team context,
and company history in the same text.
"""
import re


LEVELS = ("new-grad", "entry", "mid", "senior", "staff", "leadership", "unspecified")


def classify_experience(title, newgrad_status="unclear", references=None):
    title = str(title or "").strip()
    lower = title.lower()
    # A common IC title contains the word Staff without implying staff-level
    # scope. Remove that fixed phrase before checking level keywords.
    lower = re.sub(r"\bmember of (?:the )?technical staff\b", "", lower)
    # Product and growth functions use Lead as a business descriptor.
    lower = re.sub(r"\blead (?:ads|generation)\b", "", lower)

    # Explicit leadership titles outrank graduate language (e.g. "Head of ML,
    # New Grad Programs"). Keep this before all other title checks.
    if re.search(r"\b(?:director|head|vp|vice president|chief|manager)\b", lower):
        return _result("leadership", "title", "Title includes a leadership role.")
    if re.search(r"\bstaff\b", lower):
        return _result("staff", "title", "Title includes Staff.")
    if re.search(r"\b(?:principal|distinguished)\b", lower):
        return _result("staff", "title", "Title indicates principal or distinguished scope.")
    if re.search(r"\b(?:senior|sr\.?|lead|tech lead|team lead)\b", lower):
        return _result("senior", "title", "Title includes a senior or lead designation.")
    if re.search(r"\b(?:mid[- ]level|intermediate)\b", lower):
        return _result("mid", "title", "Title indicates mid-level scope.")
    if re.search(r"\b(?:new\s+(?:college\s+)?grad(?:uate)?|graduate)\b", lower):
        return _result("new-grad", "title", "Title indicates a new-grad or graduate role.")
    if re.search(r"\b(?:junior|jr\.?|entry[- ]level|early[- ]career)\b", lower):
        return _result("entry", "title", "Title indicates junior, entry-level, or early-career scope.")

    # Curated records may explicitly establish a new-grad pathway. Automated
    # discovery records intentionally remain unclear.
    if str(newgrad_status).lower() in {"explicit", "eligible", "confirmed", "new-grad", "newgrad", "yes"}:
        return _result("new-grad", "curated", "Curated record explicitly marks a new-grad pathway.")

    # Engineer II/III and numeric references alone are deliberately ambiguous.
    return _result("unspecified", "unknown", "No unambiguous experience level appears in the title.")


def _result(level, basis, evidence):
    return {"experienceLevel": level, "experienceLevelBasis": basis, "experienceLevelEvidence": evidence}
