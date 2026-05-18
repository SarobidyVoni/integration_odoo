# logger.py — Logging structuré par PDF

import os
from datetime import datetime


class PDFLogger:
    """Log structuré pour chaque PDF traité."""

    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.session_logs = []  # Tous les logs de la session

    def log_pdf(
        self,
        file_name: str,
        status: str,
        score: int,
        currency: str,
        rows_extracted: int,
        valid_rows: int,
        headers_detected: list,
        missing_columns: list,
        detected_issues: list,
    ) -> dict:
        """Enregistre un log structuré et retourne le dict."""

        entry = {
            "timestamp": datetime.now().isoformat(),
            "file_name": file_name,
            "status": status,
            "score": score,
            "currency": currency or "N/A",
            "rows_extracted": rows_extracted,
            "valid_rows": valid_rows,
            "headers_detected": headers_detected or [],
            "missing_columns": missing_columns or [],
            "detected_issues": detected_issues or [],
        }

        self.session_logs.append(entry)
        self._print_log(entry)
        return entry

    def _print_log(self, entry: dict):
        lines = [
            f"\n{'='*55}",
            f"FILE:        {entry['file_name']}",
            f"STATUS:      {entry['status']}",
            f"SCORE:       {entry['score']}/5",
            f"CURRENCY:    {entry['currency']}",
            f"HEADERS:     {', '.join(entry['headers_detected']) or 'N/A'}",
            f"ROWS:        {entry['rows_extracted']}",
            f"VALID_ROWS:  {entry['valid_rows']}",
        ]

        if entry["missing_columns"]:
            lines.append("ISSUES:")
            for col in entry["missing_columns"]:
                lines.append(f"  - missing column: {col}")
            for issue in entry["detected_issues"]:
                lines.append(f"  - {issue}")
        elif entry["detected_issues"]:
            lines.append("ISSUES:")
            for issue in entry["detected_issues"]:
                lines.append(f"  - {issue}")
        else:
            lines.append("ISSUES:      none")

        lines.append("=" * 55)
        print("\n".join(lines))

    def save_session_log(self):
        """Sauvegarde tous les logs dans un fichier texte horodaté."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.log_dir, f"pipeline_{ts}.log")

        with open(path, "w", encoding="utf-8") as f:
            for entry in self.session_logs:
                f.write(f"\nFILE: {entry['file_name']}\n")
                f.write(f"STATUS: {entry['status']}\n")
                f.write(f"SCORE: {entry['score']}/5\n")
                f.write(f"CURRENCY: {entry['currency']}\n")
                f.write(f"HEADERS: {', '.join(entry['headers_detected'])}\n")
                if entry["missing_columns"]:
                    f.write("ISSUES:\n")
                    for col in entry["missing_columns"]:
                        f.write(f"  - missing column: {col}\n")
                for issue in entry["detected_issues"]:
                    f.write(f"  - {issue}\n")
                f.write(f"ROWS: {entry['rows_extracted']}\n")
                f.write(f"VALID_ROWS: {entry['valid_rows']}\n")
                f.write("-" * 55 + "\n")

        print(f"\n📝 Log session sauvegardé : {path}")
        return path
