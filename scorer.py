# scorer.py — Scoring qualité d'extraction (0 à 5 points)

import re
import unicodedata
from config import BUSINESS_COLUMNS, CURRENCY_SYMBOLS, HEADER_KEYWORDS


# =========================
# UTILS (indépendants d'extract_pdf pour éviter couplage)
# =========================

def _normalize(text: str) -> str:
    text = str(text).upper()
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def _is_amount(val: str) -> bool:
    val = str(val).strip().upper()
    val = re.sub(r'(€|\$|£|MGA|AR)', '', val)
    val = val.replace(" ", "").replace("\xa0", "")
    return bool(re.match(r'^\d+([.,]\d+)?$', val))


# =========================
# SCORING PRINCIPAL
# =========================

class ScoreResult:
    def __init__(self):
        self.score = 0
        self.details = {
            "header_detected": False,
            "product_column": False,
            "quantity_column": False,
            "price_column": False,
            "amount_detected": False,
            "currency_detected": False,
            "row_coherence": False,
        }
        self.currency = None
        self.missing_columns = []
        self.detected_issues = []
        self.headers_detected = []

    @property
    def max_score(self):
        return 5


def score_extraction(table_data: list, raw_table_text: str = "") -> ScoreResult:
    """
    Évalue la qualité d'une extraction PDF.

    Critères (1 point chacun, max 5) :
      1. Header reconnu
      2. Colonne métier 'product' présente
      3. Colonne métier 'quantity' OU 'price' présente
      4. Montant numérique détecté dans les données
      5. Devise détectée + cohérence des lignes

    Args:
        table_data: liste de lignes extraites (résultat d'extract_pdf_tables)
        raw_table_text: texte brut de la table (pour détection devise)

    Returns:
        ScoreResult
    """
    result = ScoreResult()

    if not table_data:
        result.detected_issues.append("aucune ligne extraite")
        return result

    full_text = _normalize(raw_table_text or " ".join(
        " ".join(str(c) for c in row) for row in table_data
    ))

    # ── Critère 1 : header détecté ───────────────────────────────────────────
    header_score = 0
    matched_headers = []
    for category, keywords in HEADER_KEYWORDS.items():
        if any(k in full_text for k in keywords):
            header_score += 1
            matched_headers.append(category)

    if header_score >= 2:
        result.details["header_detected"] = True
        result.score += 1
        result.headers_detected = matched_headers
    else:
        result.detected_issues.append("header non reconnu ou ambigu")

    # ── Critère 2 : colonne 'product' ─────────────────────────────────────────
    if any(k in full_text for k in BUSINESS_COLUMNS["product"]):
        result.details["product_column"] = True
        result.score += 1
    else:
        result.missing_columns.append("product")

    # ── Critère 3 : colonne 'quantity' ou 'price' ────────────────────────────
    has_qty = any(k in full_text for k in BUSINESS_COLUMNS["quantity"])
    has_price = any(k in full_text for k in BUSINESS_COLUMNS["price"])

    if has_qty or has_price:
        result.details["quantity_column"] = has_qty
        result.details["price_column"] = has_price
        result.score += 1
    else:
        result.missing_columns.append("quantity")
        result.missing_columns.append("price")

    # ── Critère 4 : montant numérique détecté ────────────────────────────────
    amount_found = False
    for row in table_data:
        for cell in row:
            if _is_amount(str(cell)):
                amount_found = True
                break
        if amount_found:
            break

    if amount_found:
        result.details["amount_detected"] = True
        result.score += 1
    else:
        result.detected_issues.append("aucun montant numérique détecté")

    # ── Critère 5 : devise + cohérence des lignes ────────────────────────────
    currency_found = None
    raw_combined = raw_table_text or " ".join(
        " ".join(str(c) for c in row) for row in table_data
    )
    for symbol, name in CURRENCY_SYMBOLS.items():
        if symbol in raw_combined:
            currency_found = name
            break

    coherent_rows = sum(1 for row in table_data if len([c for c in row if str(c).strip()]) >= 3)
    row_coherence = coherent_rows >= max(1, len(table_data) * 0.5)

    if currency_found and row_coherence:
        result.details["currency_detected"] = True
        result.details["row_coherence"] = True
        result.score += 1
        result.currency = currency_found
    else:
        if not currency_found:
            result.detected_issues.append("devise non détectée")
        if not row_coherence:
            result.detected_issues.append(
                f"cohérence lignes insuffisante ({coherent_rows}/{len(table_data)})"
            )

    if currency_found and not result.currency:
        result.currency = currency_found

    return result
