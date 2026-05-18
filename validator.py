# validator.py — Validation métier des lignes extraites

import re


def normalize_quantity(value) -> float:
    """Logique originale préservée."""
    try:
        value = str(value).replace(",", ".")
        return float(value)
    except Exception:
        return 0.0


def normalize_price(value) -> str:
    """Logique originale préservée."""
    try:
        value = str(value)
        value = value.replace("$", "").replace("€", "").replace("Ar", "")
        value = value.replace(" ", "")
        value = value.replace(",", ".")
        number = float(value)
        return f"{number:.2f}".replace(".", ",")
    except Exception:
        return "0.0"


def is_timesheet_value(code: str) -> str:
    """Logique originale préservée."""
    return "TRUE" if code.startswith("CP") else "FALSE"


def determine_type_vente(code: str) -> str:
    """Logique originale préservée."""
    if code.startswith("CP"):
        return "Régie"
    elif code.startswith("LIC"):
        return "Licence"
    elif code:
        return "Forfait"
    return ""


def validate_row(row: list) -> dict:
    """
    Valide et retourne les issues détectées sur une ligne.

    Returns:
        dict avec keys: valid (bool), issues (list of str)
    """
    issues = []

    if not row:
        return {"valid": False, "issues": ["ligne vide"]}

    cleaned = [str(c).strip() for c in row if str(c).strip()]

    if len(cleaned) < 3:
        issues.append(f"trop peu de colonnes remplies ({len(cleaned)})")

    # Vérifier qu'il y a au moins un texte descriptif
    has_text = any(len(c) > 3 and not re.match(r'^\d+([.,]\d+)?$', c) for c in cleaned)
    if not has_text:
        issues.append("aucun libellé produit/service détecté")

    # Vérifier qu'il y a au moins une valeur numérique
    has_number = any(re.match(r'^\d+([.,]\d+)?$', c.replace(" ", "")) for c in cleaned)
    if not has_number:
        issues.append("aucune valeur numérique (quantité ou prix)")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }
