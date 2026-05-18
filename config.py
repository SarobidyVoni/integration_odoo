# config.py — Règles métier, mappings, headers extensibles

from datetime import datetime

# =========================
# CHEMINS
# =========================
ROOT_PATH = r"D:\Sarobidy\Projet_PULSE\ODOO\2026\2026"

OUTPUT_FILENAME = f"export/export_odoo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

# =========================
# SCORING THRESHOLDS
# =========================
SCORE_OK = 4        # score >= 4 → DATA_OK
SCORE_REVIEW = 2    # score 2–3 → DATA_REVIEW
                    # score <= 1 → PDF_ERRORS

# =========================
# COLONNES MÉTIER ATTENDUES (pour scoring)
# =========================
BUSINESS_COLUMNS = {
    "product":  ["RESOURCE", "PROFILE", "RESSOURCE", "PROFIL", "ROLE",
                 "SERVICE", "DESIGNATION", "LIBELLE", "DESCRIPTION"],
    "quantity": ["JOUR", "DAYS", "JH", "QUANTITE", "QTE", "VOLUME",
                 "NOMBRE", "NBR", "QTY", "HOMME","DAY"],
    "price":    ["RATE", "TAUX", "PRIX", "COST", "COUT", "JOURNALIER",
                 "TJM", "TARIF", "UNITAIRE", "MONTANT"],
}

# =========================
# DEVISES RECONNUES
# =========================
CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "MGA": "MGA",
    "AR": "MGA",
    "Ar": "MGA",
}

# =========================
# HEADER KEYWORDS (extensible)
# =========================
HEADER_KEYWORDS = {
    "profile":   ["RESOURCE", "PROFILE", "RESSOURCE", "PROFIL", "ROLE"],
    "rate":      ["RATE", "TAUX", "PRIX", "COST", "COUT", "JOURNALIER", "TJM"],
    "unit":      ["UNIT", "UNITE", "JOUR", "DAY", "HOMME", "JH","DAYS"],
    "id":        ["ID", "#", "NO"],
    "seniority": ["SENIORITE", "SENIORITY", "SENIOR", "EXPERT"],
    "total":     ["TOTAL", "COUT TOTAL", "MONTANT"],
}

# =========================
# COLONNES EXPORT ODOO
# =========================
ODOO_COLUMNS = [
    "ID Externe Odoo",
    "Is timesheet",
    "Condition de paiement",
    "Code projet",
    "Client",
    "Document Référence",
    "Liste de prix",
    "Type de Client",
    "Type de Vente",
    "Service Type",
    "Ligne de commande/Produit",
    "Pays de production ",
    "Ligne de commande/Quantité",
    "Ligne de commande/Unité",
    "Ligne de commande/Prix unitaire",
    "Statut",
    "Cluster",
]

# Colonnes ajoutées pour REVIEW et ERRORS
DIAGNOSTIC_COLUMN = "diagnostic_reason"

# =========================
# COULEURS EXCEL PAR ONGLET
# =========================
SHEET_COLORS = {
    "DATA_OK":     {"header_bg": "#1F4E79", "header_font": "#FFFFFF"},  # bleu foncé
    "DATA_REVIEW": {"header_bg": "#C55A11", "header_font": "#FFFFFF"},  # orange
    "PDF_ERRORS":  {"header_bg": "#C00000", "header_font": "#FFFFFF"},  # rouge
}

# =========================
# COLONNES ERREUR PDF
# =========================
PDF_ERROR_COLUMNS = ["Code projet", "Client", "Cluster", "Fichier PDF", "Erreur", DIAGNOSTIC_COLUMN]
