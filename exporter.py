# exporter.py — Export Excel colorié (DATA_OK / DATA_REVIEW / PDF_ERRORS)

import pandas as pd
from config import SHEET_COLORS, OUTPUT_FILENAME, DIAGNOSTIC_COLUMN, PDF_ERROR_COLUMNS


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _write_sheet(writer, df: pd.DataFrame, sheet_name: str, color_config: dict):
    """
    Écrit un DataFrame dans un onglet Excel avec en-tête colorié.
    """
    if df.empty:
        # Écrire un onglet vide avec une note
        empty_df = pd.DataFrame({"Info": [f"Aucune donnée dans la catégorie {sheet_name}"]})
        empty_df.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        header_format = workbook.add_format({
            "bold": True,
            "bg_color": color_config["header_bg"],
            "font_color": color_config["header_font"],
            "border": 1,
        })
        worksheet.write(0, 0, "Info", header_format)
        return

    df.to_excel(writer, sheet_name=sheet_name, index=False)
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    header_format = workbook.add_format({
        "bold": True,
        "bg_color": color_config["header_bg"],
        "font_color": color_config["header_font"],
        "border": 1,
        "text_wrap": True,
        "valign": "vcenter",
    })

    alt_row_format = workbook.add_format({
        "bg_color": "#F2F2F2",
        "border": 1,
    })

    normal_row_format = workbook.add_format({
        "bg_color": "#FFFFFF",
        "border": 1,
    })

    # En-têtes colorées
    for col_num, col_name in enumerate(df.columns):
        worksheet.write(0, col_num, col_name, header_format)
        # Largeur automatique approximative
        max_len = max(len(str(col_name)), df[col_name].astype(str).map(len).max() if not df.empty else 0)
        worksheet.set_column(col_num, col_num, min(max_len + 4, 50))

    # Alternance de couleurs sur les lignes
    for row_num in range(1, len(df) + 1):
        fmt = alt_row_format if row_num % 2 == 0 else normal_row_format
        for col_num in range(len(df.columns)):
            worksheet.write(row_num, col_num, df.iloc[row_num - 1, col_num], fmt)

    # Geler la ligne d'en-tête
    worksheet.freeze_panes(1, 0)


def export_excel(
    rows_ok: list,
    rows_review: list,
    rows_error: list,
    output_path: str = None,
) -> str:
    """
    Génère le fichier Excel final avec 3 onglets colorés.

    Args:
        rows_ok:     lignes DATA_OK
        rows_review: lignes DATA_REVIEW (avec diagnostic_reason)
        rows_error:  lignes PDF_ERRORS (avec diagnostic_reason)
        output_path: chemin de sortie (défaut: config.OUTPUT_FILENAME)

    Returns:
        str: chemin du fichier généré
    """
    output_path = output_path or OUTPUT_FILENAME

    df_ok = pd.DataFrame(rows_ok)
    df_review = pd.DataFrame(rows_review)
    df_error = pd.DataFrame(rows_error)

    # S'assurer que diagnostic_reason est présent dans review et error
    for df in [df_review, df_error]:
        if not df.empty and DIAGNOSTIC_COLUMN not in df.columns:
            df[DIAGNOSTIC_COLUMN] = ""

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        _write_sheet(writer, df_ok, "DATA_OK", SHEET_COLORS["DATA_OK"])
        _write_sheet(writer, df_review, "DATA_REVIEW", SHEET_COLORS["DATA_REVIEW"])
        _write_sheet(writer, df_error, "PDF_ERRORS", SHEET_COLORS["PDF_ERRORS"])

    print(f"\n✔ Excel généré : {output_path}")
    print(f"  DATA_OK     : {len(rows_ok)} ligne(s)")
    print(f"  DATA_REVIEW : {len(rows_review)} ligne(s)")
    print(f"  PDF_ERRORS  : {len(rows_error)} ligne(s)")

    return output_path
