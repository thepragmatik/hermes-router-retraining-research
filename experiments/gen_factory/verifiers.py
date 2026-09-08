#!/usr/bin/env python3
"""Deterministic verifiers for verifier-by-construction items (R0, $0).

`run_verifier(verifier, answer_text) -> bool` executes the machine-checkable
verifier the generator emitted with its item. NEVER raises: any malformed
verifier, unparseable answer, or unexpected type returns False (a False label
must never crash the labeling loop, and a verifier failure is just a
`weak_ok=False`).

Verifier types
--------------
exact_match
    Case/whitespace-normalized substring containment of the verifier value
    inside the answer's FINAL-ANSWER REGION. Normalization documented in
    `_norm`: unicode NFKC, casefold (strict case folding), collapse of all
    whitespace runs to a single space, and strip. This intentionally accepts
    inflected/embedded answers ("...capital is Paris.") while the
    final-answer-region extraction below prevents a bare mention of the
    answer in early reasoning text from passing.
numeric_tol
    Extract the FIRST number in the final-answer region of `answer_text`
    (int/float/scientific; a leading '-' or '+' binds to the number; an
    internal comma separator like 1,234.5 is tolerated). Compare
    abs(extracted - value) <= tol; tol defaults to 1e-6 when the verifier
    omits it.

Final-answer region
-------------------
If the answer contains a "final answer" / "answer:" marker (case-insensitive),
the region is everything after the LAST such marker; otherwise the region is
the last non-empty line of the answer. Numbers for numeric_tol are searched in
that region first; if the region yields no number we fall back to the whole
answer (models sometimes omit the marker on short numeric answers).
"""
import re
import unicodedata

DEFAULT_TOL = 1e-6

# "final answer", "answer:", "the final answer is" ... last occurrence wins.
# The match ends AT the marker (optional trailing "is"/colon) — never past it,
# so the region after the marker keeps the answer text.
_FINAL_MARKER = re.compile(
    r"(?:the\s+)?final\s+answer\b(?:\s+is)?\s*[:\-]?\s*|answer\s*[:\-]\s*",
    re.I)
# Number: optional sign, digits with optional thousands commas, optional
# fraction, optional exponent. Tried first in the final-answer region.
_NUM = re.compile(
    r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?")
_FALLBACK_NUM = re.compile(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def _norm(s):
    """NFKC -> casefold -> collapse whitespace runs to one space -> strip."""
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", s).strip()


def _final_region(answer_text):
    """Everything after the last final-answer marker, else last non-empty line."""
    hits = list(_FINAL_MARKER.finditer(answer_text))
    if hits:
        return answer_text[hits[-1].end():]
    lines = [ln for ln in answer_text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def _to_float(s):
    try:
        return float(s.replace(",", ""))
    except (TypeError, ValueError):
        return None


def _num_in(region, fallback_text):
    m = _NUM.search(region) or _FALLBACK_NUM.search(fallback_text)
    if m is None:
        return None
    return _to_float(m.group(0))


def _verify_exact_match(value, answer_text):
    # Non-string verifier value -> False (bool is an int subclass; the spec
    # says non-string values must fail, and True/"" are degenerate).
    if not isinstance(value, str) or isinstance(value, bool):
        return False
    if not value.strip():
        return False
    if not isinstance(answer_text, str):
        return False
    return _norm(value) in _norm(_final_region(answer_text))


def _verify_numeric_tol(verifier, answer_text):
    value = verifier.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return False
    target = _to_float(value) if isinstance(value, str) else float(value)
    if target is None or target != target:  # NaN / unparseable
        return False
    tol = verifier.get("tol", DEFAULT_TOL)
    if isinstance(tol, bool) or not isinstance(tol, (int, float)):
        return False
    tol = float(tol)
    if tol != tol or tol < 0:
        return False
    if not isinstance(answer_text, str):
        return False
    region = _final_region(answer_text)
    num = _num_in(region, answer_text)
    if num is None:
        return False
    return abs(num - target) <= tol


def _tokens(s):
    """Lowercase [a-z0-9] tokens minus prereg stopwords (R4 token_set)."""
    stop = {"the", "a", "an", "is", "are", "of", "to", "in", "and",
            "or", "that", "it"}
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in stop}


def _verify_token_set(verifier, answer_text):
    """Normalized token-set overlap >= threshold (default 0.8). Overlap is
    measured on the verifier VALUE's tokens found in the answer's
    final-answer region (set intersection / |value tokens|)."""
    want = _tokens(str(verifier.get("value", "")))
    if not want:
        return False
    if not isinstance(answer_text, str):
        return False
    got = _tokens(_final_region(answer_text))
    overlap = len(want & got) / len(want)
    thr = verifier.get("threshold", 0.8)
    if isinstance(thr, bool) or not isinstance(thr, (int, float)):
        return False
    thr = float(thr)
    if thr != thr:
        return False
    return overlap >= thr


def run_verifier(verifier, answer_text):
    """Execute a verifier dict against an answer. Returns bool, never raises."""
    try:
        if not isinstance(verifier, dict):
            return False
        vtype = verifier.get("type")
        if vtype == "exact_match":
            return _verify_exact_match(verifier.get("value"), answer_text)
        if vtype == "numeric_tol":
            return _verify_numeric_tol(verifier, answer_text)
        if vtype == "token_set":
            return _verify_token_set(verifier, answer_text)
        return False
    except Exception:
        return False
