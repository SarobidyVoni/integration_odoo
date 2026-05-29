import os

from config import ROOT_PATH, DIAGNOSTIC_COLUMN
from extractor import extract
from scorer import score_extraction
from classifier import classify, build_diagnostic
from validator import (
    normalize_quantity,
    normalize_price,
    is_timesheet_value,
    determine_type_vente,
)
from logger import PDFLogger
from exporter import export_excel


logger = PDFLogger(log_dir="logs")

rows_ok, rows_review, rows_error = [], [], []


# =========================
# HELPERS
# =========================

def empty_project_row(code_projet, client, document_reference, type_client, cluster, diagnostic=""):
    row = {
        "ID Externe Odoo": "",
        "Is timesheet": is_timesheet_value(code_projet),
        "Condition de paiement": "30 jours après facture" if code_projet.strip() else "0",
        "Code projet": code_projet,
        "Client": client,
        "Document Référence": document_reference,
        "Liste de prix": "",
        "Type de Client": type_client,
        "Type de Vente": determine_type_vente(code_projet),
        "Service Type": "",
        "Ligne de commande/Produit": "",
        "Pays de production ": "Madagascar",
        "Ligne de commande/Quantité": 0.0,
        "Ligne de commande/Unité": "Jour Homme",
        "Ligne de commande/Prix unitaire": 0.0,
        "Statut": "NOK",
        "Cluster": cluster,
    }
    if diagnostic:
        row[DIAGNOSTIC_COLUMN] = diagnostic
    return row


def find_folder_containing(parent_path, keyword):
    keyword = keyword.upper()
    if not os.path.exists(parent_path):
        return None
    for folder in os.listdir(parent_path):
        full_path = os.path.join(parent_path, folder)
        if os.path.isdir(full_path) and keyword in folder.upper():
            return full_path
    return None


def route_row(row: dict, category: str):
    if category == "DATA_OK":
        rows_ok.append(row)
    elif category == "DATA_REVIEW":
        rows_review.append(row)
    else:
        rows_error.append(row)


# =========================
# ✅ NOUVEAU : détection devise
# =========================

def detect_currency(text: str) -> str:
    if "$" in text:
        return "USD"
    if "€" in text:
        return "EUR"
    if "MGA" in text or " Ar " in text:
        return "MGA"
    return ""


# =========================
# MAIN LOOP
# =========================

for type_client in os.listdir(ROOT_PATH):
    type_path = os.path.join(ROOT_PATH, type_client)
    if not os.path.isdir(type_path):
        continue

    for cluster in os.listdir(type_path):
        cluster_path = os.path.join(type_path, cluster)
        if not os.path.isdir(cluster_path):
            continue

        for client in os.listdir(cluster_path):
            client_path = os.path.join(cluster_path, client)
            if not os.path.isdir(client_path):
                continue

            has_project = False

            # ✅ CAS : client sans projet
            if not any(os.path.isdir(os.path.join(client_path, d)) for d in os.listdir(client_path)):
                diagnostic = "Client non associé à un projet"
                row = empty_project_row("N/A", client, "", type_client, cluster, diagnostic)

                logger.log_pdf(
                    file_name=f"{client} [no project]",
                    status="PDF_ERRORS",
                    score=0,
                    currency=None,
                    rows_extracted=0,
                    valid_rows=0,
                    headers_detected=[],
                    missing_columns=["project folder"],
                    detected_issues=[diagnostic],
                )

                rows_error.append(row)
                continue

            for code_projet in os.listdir(client_path):
                projet_path = os.path.join(client_path, code_projet)

                if not os.path.isdir(projet_path):
                    continue

                has_project = True

                bc_path = find_folder_containing(projet_path, "BC")
                devis_path = find_folder_containing(projet_path, "DEVIS")

                bc_files = [] if not bc_path else [f for f in os.listdir(bc_path) if f.lower().endswith(".pdf")]
                devis_files = [] if not devis_path else [f for f in os.listdir(devis_path) if f.lower().endswith(".pdf")]

                document_reference = ",".join(bc_files + devis_files)

                # =========================
                # Cas sans devis
                # =========================
                if not devis_path:
                    diagnostic = "dossier DEVIS absent"
                    row = empty_project_row(code_projet, client, document_reference, type_client, cluster, diagnostic)

                    logger.log_pdf(
                        file_name=f"{code_projet} [no devis]",
                        status="PDF_ERRORS",
                        score=0,
                        currency=None,
                        rows_extracted=0,
                        valid_rows=0,
                        headers_detected=[],
                        missing_columns=["devis folder"],
                        detected_issues=[diagnostic],
                    )
                    rows_error.append(row)
                    continue

                if not devis_files:
                    diagnostic = "dossier DEVIS vide (aucun PDF)"
                    row = empty_project_row(code_projet, client, document_reference, type_client, cluster, diagnostic)

                    logger.log_pdf(
                        file_name=f"{code_projet} [empty devis]",
                        status="PDF_ERRORS",
                        score=0,
                        currency=None,
                        rows_extracted=0,
                        valid_rows=0,
                        headers_detected=[],
                        missing_columns=["pdf files"],
                        detected_issues=[diagnostic],
                    )
                    rows_error.append(row)
                    continue

                # =========================
                # Traitement PDF
                # =========================
                for file in devis_files:
                    pdf_path = os.path.join(devis_path, file)

                    table_data, headers = extract(pdf_path)

                    # ✅ FIX : .values() pour itérer sur les valeurs du dict (pas les clés)
                    raw_text = " ".join(
                        " ".join(str(v) for v in row.values())
                        for row in table_data
                    ) if table_data else ""

                    # === adaptation scoring
                    table_data_for_score = [
                        [row.get("product", ""),
                         row.get("quantity", ""),
                         row.get("price_raw", row.get("price", ""))]
                        for row in table_data
                    ]

                    headers_text = " ".join(
                        " ".join(str(h) for h in header if h)
                        for header in headers
                    ) if headers else ""

                    # ✅ FIX : on inclut aussi table_data_for_score pour capturer $196 etc.
                    score_rows_text = " ".join(
                        " ".join(str(c) for c in row) for row in table_data_for_score
                    )

                    raw_text_enriched = headers_text + " " + raw_text + " " + score_rows_text

                    # ✅ DEBUG CONSERVÉ (devise)
                    print("\n🔍 DEBUG CURRENCY SOURCE:")
                    for symbol in ["$", "€", "MGA", "AR"]:
                        if symbol in raw_text_enriched:
                            print(f"FOUND SYMBOL: {symbol}")

                    # ==== DEBUG LIGNES ANALYSÉES ====
                    print("\n🔍 DEBUG SCORING INPUT")

                    for i, row in enumerate(table_data_for_score):
                        print(f"ROW {i}:", row)

                    print("\n👉 HEADERS TEXT:")
                    print(headers_text)

                    print("\n👉 RAW TEXT ENRICHED:")
                    print(raw_text_enriched[:500])  # limite affichage

                    # ==== DEBUG DEVISE PAR LIGNE ====
                    print("\n🔍 CHECK CURRENCY PAR LIGNE")

                    for i, row in enumerate(table_data_for_score):
                        row_text = " ".join(str(c) for c in row)
                        found = [s for s in ["$", "€", "MGA", "AR"] if s in row_text]

                        print(f"ROW {i} TEXT:", row_text)
                        print(f"→ SYMBOLS FOUND:", found if found else "NONE")

                    # ==== SCORING ====
                    score_result = score_extraction(table_data_for_score, raw_text_enriched)

                    category = classify(score_result.score)
                    diagnostic = build_diagnostic(score_result) if category != "DATA_OK" else ""

                    logger.log_pdf(
                        file_name=file,
                        status=category,
                        score=score_result.score,
                        currency=score_result.currency,
                        rows_extracted=len(table_data),
                        valid_rows=len(table_data),
                        headers_detected=score_result.headers_detected,
                        missing_columns=score_result.missing_columns,
                        detected_issues=score_result.detected_issues,
                    )

                    if not table_data or category == "PDF_ERRORS":
                        rows_error.append(
                            empty_project_row(
                                code_projet,
                                client,
                                document_reference,
                                type_client,
                                cluster,
                                diagnostic or "Aucune table exploitable détectée",
                            )
                        )
                        continue

                    # ✅ FIX : on utilise detect_currency() sur raw_text_enriched
                    #          qui contient maintenant les valeurs avec symboles ($, €, MGA)
                    currency_label = (
                        score_result.currency
                        if score_result.currency and score_result.currency not in ("N/A", "Non trouvé", None, "")
                        else detect_currency(raw_text_enriched)
                    )

                    print(f"\n💰 CURRENCY LABEL FINAL: {currency_label}")

                    for row in table_data:
                        odoo_row = {
                            "ID Externe Odoo": "",
                            "Is timesheet": is_timesheet_value(code_projet),
                            "Condition de paiement": "30 jours après facture" if code_projet.strip() else "0",
                            "Code projet": code_projet,
                            "Client": client,
                            "Document Référence": document_reference,
                            "Liste de prix": currency_label,
                            "Type de Client": type_client,
                            "Type de Vente": determine_type_vente(code_projet),
                            "Service Type": "",
                            "Ligne de commande/Produit": row.get("product", ""),
                            "Pays de production ": "Madagascar",
                            "Ligne de commande/Quantité": normalize_quantity(row.get("quantity", "")),
                            "Ligne de commande/Unité": "Jour Homme",
                            "Ligne de commande/Prix unitaire": normalize_price(row.get("price", "")),
                            "Statut": "NOK",
                            "Cluster": cluster,
                        }

                        if category != "DATA_OK":
                            odoo_row[DIAGNOSTIC_COLUMN] = diagnostic

                        route_row(odoo_row, category)

# =========================
# EXPORT
# =========================
export_excel(rows_ok, rows_review, rows_error)

# =========================
# LOG SESSION
# =========================
logger.save_session_log()

print("\n✔ Pipeline terminé.")
print(f"  DATA_OK     : {len(rows_ok)}")
print(f"  DATA_REVIEW : {len(rows_review)}")
print(f"  PDF_ERRORS  : {len(rows_error)}")