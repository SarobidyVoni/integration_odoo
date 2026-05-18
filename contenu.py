import pdfplumber

PDF_PATH = r"D:\Sarobidy\Projet_PULSE\ODOO\2026\2026\GROUP\AXIAN TELECOM\Yas MG\LIC-YasMG-BIReporting2026\DEVIS\YASMG2603110- DEVIS - Rajout Licences Sage BI Reporting - 5Users.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"\n📄 TOTAL PAGES: {len(pdf.pages)}")

    for i, page in enumerate(pdf.pages):
        print(f"\n================ PAGE {i+1} ================\n")

        # ✅ extraction robuste des tables (LINES d'abord)
        tables = page.extract_tables({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines"
        })

        # ✅ fallback si aucune table trouvée
        if not tables:
            print("⚠️ Aucun tableau (LINES), tentative en mode TEXT...\n")

            tables = page.extract_tables({
                "vertical_strategy": "text",
                "horizontal_strategy": "text"
            })

        # ✅ affichage
        if tables:
            print(f"✅ {len(tables)} table(s) détectée(s)\n")

            for t_idx, table in enumerate(tables):
                print(f"\n📋 TABLE {t_idx + 1}:\n")

                for row in table:
                    print(row)

                print("\n-----------------------------------\n")
        else:
            print("❌ Aucune table détectée sur cette page\n")