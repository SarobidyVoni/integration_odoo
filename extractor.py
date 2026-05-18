# extractor.py — Extraction PDF (logique originale inchangée)
# Délègue entièrement à extract_pdf.py existant.

from extract_pdf import extract_pdf_tables  # noqa: F401 — logique originale préservée


def extract(pdf_path: str) -> list:
    """
    Point d'entrée unique pour l'extraction PDF.
    Délègue à extract_pdf_tables sans modifier sa logique.

    Returns:
        list of rows (each row is a list of cell values)
        Empty list si aucune table exploitable détectée.
    """
    try:
        result = extract_pdf_tables(pdf_path)
        return result if result else []
    except Exception as e:
        print(f"  ⚠️  Erreur extraction PDF [{pdf_path}]: {e}")
        return []
