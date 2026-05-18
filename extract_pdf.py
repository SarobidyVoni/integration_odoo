import pdfplumber, re, unicodedata
from collections import defaultdict

DEBUG = True
def log(x): 
    if DEBUG: print(x)

def normalize(t):
    return ''.join(c for c in unicodedata.normalize('NFD', str(t).upper())
                   if unicodedata.category(c) != 'Mn')

def clean_amount(v):
    v = re.sub(r'(€|\$|£|MGA|AR)', '', str(v))
    v = v.replace(" ", "").replace("\xa0", "").replace(",", ".")
    try: return float(v)
    except: return None


def is_amount(val):
    val = re.sub(r'(€|\$|£|MGA|AR)', '', str(val)).replace(" ", "")
    return bool(re.match(r'^\d+([.,]\d+)?$', val))

def resolve_header_mapping(header):
    text = normalize(" ".join(str(x) for x in header if x))
    text = re.sub(r'\s+', ' ', text)

    # ===== CAS FUSIONNÉ
    if len([x for x in header if x]) == 1:
        words = text.split()
        mapping = {}
        for i, w in enumerate(words):
            if w in ["DESCRIPTION", "PROFILE", "RESOURCE", "PROFIL","DESCRIPTIONS","DESIGNATION","LIBELLE","REPARTITION","REPARTITION DES COUTS"]:
                mapping["product"] = i

            # ✅ PRICE AVANT QUANTITY
            elif w in ["RATE", "PRIX", "TAUX", "COST", "TJM","COUT"]:
                mapping["price"] = i

            elif w in ["DAY", "DAYS", "JOUR", "JH", "UNITE", "UNIT","UNITES"]:
                mapping["quantity"] = i

        return mapping

    # ===== CAS NORMAL
    mapping = {}

    for i, c in enumerate(header):
        t = normalize(c)
        t = re.sub(r'[^A-Z ]', ' ', t)

        # ✅ PRODUCT
        if any(k in t for k in ["PROFILE","RESOURCE","DESCRIPTION","PROFIL"]):
            mapping["product"] = i

        # ✅ PRICE AVANT QUANTITY (🔥 FIX PRINCIPAL)
        elif any(k in t for k in ["RATE","PRIX","TAUX","COST","TJM"]):
            mapping["price"] = i

        # ✅ UTILISER t (PAS text)
        elif any(k in t for k in [
            "DAY", "DAYS", "JOUR", "JH",
            "JOURS", "HOMME", "JOURHOMME",
            "UNITE", "UNIT"
        ]):
            mapping["quantity"] = i

    return mapping


def is_header_row(row):
    text = normalize(" ".join(str(x) for x in row if x))
    kws = ["PROFILE","RESOURCE","DESCRIPTION","RATE","PRIX","DAY","JOUR","JH","TOTAL"]
    score = sum(1 for k in kws if k in text)

    non_empty = [x for x in row if str(x).strip()]
    num = sum(1 for x in non_empty if is_amount(x))

    return score >= 2 and (len(non_empty)==0 or num/len(non_empty) <= 0.3)

def find_header_index(table):
    for i, r in enumerate(table):
        if is_header_row(r): return i
    return None

def split_merged_table(table):
    seg, cur = [], None
    for i, r in enumerate(table):
        if is_header_row(r):
            if cur is not None: seg.append((cur, i-1))
            cur = i
    if cur is not None: seg.append((cur, len(table)-1))
    return [table[s:e+1] for s,e in seg] if seg else [table]

def clean_row(row):
    row = [str(x).strip() if x else "" for x in row]
    while row and row[-1]=="":
        row.pop()
    return row if sum(1 for x in row if x)>1 else None

def is_valid_product_row(row):
    txt = normalize(" ".join(row))
    if any(k in txt for k in ["TOTAL","SUBTOTAL"]): return False
    return any(is_amount(x) for x in row) and any(len(x)>5 and not is_amount(x) for x in row)

# ===== ✅ NOUVEAU : conversion ligne -> dict
def build_row_dict(row, mapping):
    try:
        product = row[mapping["product"]] if "product" in mapping else None
        quantity = row[mapping["quantity"]] if "quantity" in mapping else None
        price = row[mapping["price"]] if "price" in mapping else None

        return {
            "product": product,
            "quantity": quantity,
            "price": price
        }
    except:
        return None

def reconstruct_table(page):
    words = page.extract_words(use_text_flow=True)
    lines = defaultdict(list)
    for w in words:
        lines[round(w['top'],1)].append(w)
    return [[w['text'] for w in sorted(v,key=lambda x:x['x0'])] for k,v in sorted(lines.items())]

def extract_tables_robust(page):
    t = page.extract_tables({"vertical_strategy":"lines","horizontal_strategy":"lines"})
    if t: return t
    t = page.extract_tables({"vertical_strategy":"text","horizontal_strategy":"text"})
    if t: return t
    return [reconstruct_table(page)]

# ===== MAIN
def extract_pdf_tables(pdf_path):
    results = []
    detected_headers = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in extract_tables_robust(page):
                for sub in split_merged_table(table):

                    hi = find_header_index(sub)
                    if hi is None: 
                        continue

                    header = sub[hi]
                    detected_headers.append(header)   # ✅ IMPORTANT

                    mapping = resolve_header_mapping(header)

                    # log(f"\nHEADER: {header}")
                    # log(f"MAPPING: {mapping}")

                    for row in sub[hi+1:]:
                        r = clean_row(row)
                        if not r or not is_valid_product_row(r):
                            continue

                        d = build_row_dict(r, mapping)
                        if d:
                            results.append(d)
                            # log(f"✅ {d}")

    return results, detected_headers   # ✅ ICI LE FIX

# =========================
# TEST
# =========================
if __name__ == "__main__":
    results = extract_pdf_tables(
        r"D:\Sarobidy\Projet_PULSE\ODOO\2026\2026\GROUP\AXIAN ENERGY\NEA\CP-OPS-MigrationMSIntune\DEVIS\Devis_NEA_SN_INTUNE_15122025.pdf"
    )

    print("\n=== RÉSULTATS FINAUX ===")
    for item in results:
        print(item)

