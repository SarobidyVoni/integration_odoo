# classifier.py — Classification par score

from config import SCORE_OK, SCORE_REVIEW


def classify(score: int) -> str:
    """
    Retourne la catégorie selon le score.

    score >= SCORE_OK   → DATA_OK
    score >= SCORE_REVIEW → DATA_REVIEW
    score <  SCORE_REVIEW → PDF_ERRORS
    """
    if score >= SCORE_OK:
        return "DATA_OK"
    elif score >= SCORE_REVIEW:
        return "DATA_REVIEW"
    else:
        return "PDF_ERRORS"


def build_diagnostic(score_result) -> str:
    """
    Construit le message de diagnostic pour les colonnes REVIEW / ERRORS.
    """
    parts = []

    if not score_result.details.get("header_detected"):
        parts.append("header non reconnu")

    for col in score_result.missing_columns:
        parts.append(f"colonne manquante: {col}")

    for issue in score_result.detected_issues:
        parts.append(issue)

    if not parts:
        parts.append("données incomplètes")

    return " | ".join(parts)
