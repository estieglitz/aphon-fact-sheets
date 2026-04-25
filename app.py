from flask import Flask, request, send_file, jsonify, render_template_string
from pypdf import PdfReader, PdfWriter
import io
import json
import os

app = Flask(__name__)

# The source PDF must be placed alongside this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_PDF = os.path.join(BASE_DIR, "source.pdf")

# ---------------------------------------------------------------------------
# Medication index: canonical name -> {en: [1-indexed pages], es: [1-indexed pages]}
# ---------------------------------------------------------------------------
MEDICATION_INDEX = {
  "Activated Prothrombin Complex Concentrate": {"en": [3], "es": [139]},
  "Activated Recombinant Factor VII": {"en": [4], "es": [140]},
  "Acyclovir": {"en": [5], "es": [141]},
  "Aldesleukin": {"en": [6], "es": [142]},
  "Alemtuzumab": {"en": [7], "es": [143, 144]},
  "Allopurinol": {"en": [8], "es": [145]},
  "Amifostine": {"en": [9], "es": [146]},
  "Aminocaproic Acid": {"en": [10], "es": [147]},
  "Antithymocyte Globulin": {"en": [11], "es": [148]},
  "Aprepitant/Fosaprepitant": {"en": [12], "es": [149]},
  "Arsenic Trioxide": {"en": [13, 14], "es": [150, 151]},
  "Asparaginase": {"en": [15], "es": [152]},
  "Atovaquone": {"en": [16], "es": [153]},
  "Bevacizumab": {"en": [17], "es": [154]},
  "Bleomycin": {"en": [18], "es": [155]},
  "Blinatumomab": {"en": [19, 20], "es": [156, 157]},
  "Busulfan": {"en": [21], "es": [158]},
  "Carboplatin": {"en": [22], "es": [159]},
  "Carmustine": {"en": [23], "es": [160]},
  "Caspofungin": {"en": [24], "es": [161]},
  "Cidofovir": {"en": [25], "es": [162]},
  "Cisplatin": {"en": [26], "es": [163]},
  "Cladribine": {"en": [27], "es": [164]},
  "Clofarabine": {"en": [28, 29], "es": [165, 166]},
  "Colony Stimulating Factors (CSF)": {"en": [30], "es": [167]},
  "Co-Trimoxazole: Sulfamethoxazole/Trimethoprim": {"en": [31], "es": [168]},
  "Cyclophosphamide": {"en": [32], "es": [169]},
  "Cyclosporine": {"en": [33], "es": [170]},
  "Cytarabine": {"en": [34], "es": [171]},
  "Dacarbazine": {"en": [35], "es": [172]},
  "Daclizumab": {"en": [36], "es": [173]},
  "Dactinomycin": {"en": [37], "es": [174]},
  "Dapsone": {"en": [38], "es": [175]},
  "Dasatinib": {"en": [39, 40], "es": [176, 177]},
  "Daunorubicin": {"en": [41], "es": [178]},
  "Deferasirox": {"en": [42], "es": [179]},
  "Deferoxamine": {"en": [43], "es": [180]},
  "Defibrotide": {"en": [44], "es": [181]},
  "Denileukin Diftitox": {"en": [45], "es": [182]},
  "Desmopressin Acetate": {"en": [46], "es": [183]},
  "Dexamethasone": {"en": [47], "es": [184]},
  "Dexrazoxane": {"en": [48], "es": [185]},
  "Dinutuximab": {"en": [49], "es": [186]},
  "Docetaxel": {"en": [50], "es": [187]},
  "Doxorubicin": {"en": [51], "es": [188]},
  "Eculizumab": {"en": [52], "es": [189]},
  "Enoxaparin": {"en": [53], "es": [190]},
  "Epratuzumab": {"en": [54], "es": [191]},
  "Erlotinib": {"en": [55], "es": [192, 193]},
  "Etanercept": {"en": [56], "es": [194]},
  "Etoposide": {"en": [57], "es": [195]},
  "Everolimus": {"en": [58, 59], "es": [196, 197]},
  "Fluconazole": {"en": [60], "es": [198]},
  "Fludarabine": {"en": [61], "es": [199]},
  "Fluorouracil": {"en": [62], "es": [200]},
  "Folic Acid": {"en": [63], "es": [201]},
  "Foscarnet": {"en": [64], "es": [202]},
  "Gabapentin": {"en": [65], "es": [203]},
  "Ganciclovir": {"en": [66], "es": [204]},
  "Gemcitabine": {"en": [67], "es": [205]},
  "Gemtuzumab Ozogamicin": {"en": [68], "es": [206]},
  "Glucarpidase": {"en": [69], "es": [207]},
  "Glutamine": {"en": [70], "es": [208]},
  "Granisetron": {"en": [71], "es": [209]},
  "Histamine H2 Antagonist": {"en": [72], "es": [210]},
  "Hydrocortisone": {"en": [73], "es": [211]},
  "Hydroxyurea": {"en": [74], "es": [212]},
  "Hydroxyzine": {"en": [75], "es": [213]},
  "Idarubicin": {"en": [76], "es": [214]},
  "Ifosfamide": {"en": [77], "es": [215]},
  "Imatinib Mesylate": {"en": [78], "es": [216]},
  "Indomethacin": {"en": [79], "es": [217]},
  "Infliximab": {"en": [80], "es": [218, 219]},
  "Interferon": {"en": [81], "es": [220]},
  "Intravenous Immune Globulin": {"en": [82], "es": [221]},
  "Irinotecan": {"en": [83], "es": [222]},
  "Isotretinoin": {"en": [84, 85], "es": [223, 224]},
  "Ketorolac": {"en": [86], "es": [225]},
  "Leucovorin": {"en": [87], "es": [226]},
  "Liposomal Amphotericin B": {"en": [88], "es": [227]},
  "Liposomal Cytarabine": {"en": [89], "es": [228]},
  "Liposomal Doxorubicin": {"en": [90], "es": [229]},
  "Lomustine": {"en": [91], "es": [230]},
  "Lorazepam": {"en": [92], "es": [231]},
  "Mechlorethamine": {"en": [93], "es": [232]},
  "Melphalan": {"en": [94], "es": [233]},
  "Mercaptopurine": {"en": [95], "es": [234]},
  "Mesna": {"en": [96], "es": [235]},
  "Methotrexate": {"en": [97], "es": [236]},
  "Micafungin": {"en": [98], "es": [237]},
  "Mitoxantrone": {"en": [99], "es": [238]},
  "Mycophenolate": {"en": [100], "es": [239]},
  "Nelarabine": {"en": [101], "es": [240]},
  "Nilotinib": {"en": [102], "es": [241, 242]},
  "Nystatin/Clotrimazole": {"en": [103], "es": [243]},
  "Ondansetron": {"en": [104], "es": [244]},
  "Oxaliplatin": {"en": [105], "es": [245]},
  "Paclitaxel": {"en": [106], "es": [246]},
  "Pemetrexed": {"en": [107], "es": [247]},
  "Pentamidine": {"en": [108], "es": [248]},
  "Pentostatin": {"en": [109], "es": [249]},
  "Plerixafor": {"en": [110], "es": [250]},
  "Prednisone": {"en": [111], "es": [251]},
  "Procarbazine": {"en": [112], "es": [252]},
  "Propranolol": {"en": [113], "es": [253]},
  "Proton Pump Inhibitors": {"en": [114], "es": [254]},
  "Rasburicase": {"en": [115], "es": [255]},
  "Recombinant Factor IX": {"en": [116], "es": [256]},
  "Recombinant Factor VIII": {"en": [117], "es": [257]},
  "Rho(D) Immune Globulin": {"en": [118], "es": [258]},
  "Rituximab": {"en": [119], "es": [259]},
  "Sirolimus": {"en": [120], "es": [260]},
  "Sorafenib": {"en": [121], "es": [261]},
  "Tacrolimus": {"en": [122], "es": [262]},
  "Temozolomide": {"en": [123], "es": [263]},
  "Temsirolimus": {"en": [124], "es": [264]},
  "Thalidomide": {"en": [125], "es": [265]},
  "Thioguanine": {"en": [126], "es": [266]},
  "Thiotepa": {"en": [127, 128], "es": [267, 268]},
  "Topotecan": {"en": [129], "es": [269]},
  "Trastuzumab": {"en": [130], "es": [270]},
  "Ursodiol": {"en": [131], "es": [271]},
  "Valacyclovir": {"en": [132], "es": [272]},
  "Vinblastine": {"en": [133], "es": [273]},
  "Vincristine": {"en": [134], "es": [274]},
  "Vinorelbine": {"en": [135], "es": [275]},
  "Voriconazole": {"en": [136], "es": [276]},
  "Vorinostat": {"en": [137], "es": [277]},
  "Warfarin": {"en": [138], "es": [278]},
}

# Alias map: lowercase alias -> canonical name
ALIASES = {
    "bactrim": "Co-Trimoxazole: Sulfamethoxazole/Trimethoprim",
    "septra": "Co-Trimoxazole: Sulfamethoxazole/Trimethoprim",
    "trimethoprim": "Co-Trimoxazole: Sulfamethoxazole/Trimethoprim",
    "sulfamethoxazole": "Co-Trimoxazole: Sulfamethoxazole/Trimethoprim",
    "tmp-smx": "Co-Trimoxazole: Sulfamethoxazole/Trimethoprim",
    "tmp/smx": "Co-Trimoxazole: Sulfamethoxazole/Trimethoprim",
    "g-csf": "Colony Stimulating Factors (CSF)",
    "gm-csf": "Colony Stimulating Factors (CSF)",
    "filgrastim": "Colony Stimulating Factors (CSF)",
    "pegfilgrastim": "Colony Stimulating Factors (CSF)",
    "neupogen": "Colony Stimulating Factors (CSF)",
    "neulasta": "Colony Stimulating Factors (CSF)",
    "feiba": "Activated Prothrombin Complex Concentrate",
    "novoseven": "Activated Recombinant Factor VII",
    "novo seven": "Activated Recombinant Factor VII",
    "ivig": "Intravenous Immune Globulin",
    "immune globulin": "Intravenous Immune Globulin",
    "amphotericin": "Liposomal Amphotericin B",
    "ambisome": "Liposomal Amphotericin B",
    "ara-c": "Cytarabine",
    "cytosine arabinoside": "Cytarabine",
    "5-fu": "Fluorouracil",
    "5fu": "Fluorouracil",
    "mtx": "Methotrexate",
    "6-mp": "Mercaptopurine",
    "6mp": "Mercaptopurine",
    "6-tg": "Thioguanine",
    "6tg": "Thioguanine",
    "actinomycin": "Dactinomycin",
    "actinomycin d": "Dactinomycin",
    "adriamycin": "Doxorubicin",
    "gleevec": "Imatinib Mesylate",
    "imatinib": "Imatinib Mesylate",
    "rituxan": "Rituximab",
    "herceptin": "Trastuzumab",
    "avastin": "Bevacizumab",
    "taxol": "Paclitaxel",
    "taxotere": "Docetaxel",
    "hydrea": "Hydroxyurea",
    "prograf": "Tacrolimus",
    "rapamune": "Sirolimus",
    "coumadin": "Warfarin",
    "ativan": "Lorazepam",
    "zofran": "Ondansetron",
    "decadron": "Dexamethasone",
    "solu-medrol": "Hydrocortisone",
    "solu-cortef": "Hydrocortisone",
    "valtrex": "Valacyclovir",
    "zovirax": "Acyclovir",
    "diflucan": "Fluconazole",
    "cancidas": "Caspofungin",
    "mycamine": "Micafungin",
    "vfend": "Voriconazole",
    "alkeran": "Melphalan",
    "cytoxan": "Cyclophosphamide",
    "ifex": "Ifosfamide",
    "platinol": "Cisplatin",
    "paraplatin": "Carboplatin",
    "eloxatin": "Oxaliplatin",
    "oncovin": "Vincristine",
    "navelbine": "Vinorelbine",
    "velbe": "Vinblastine",
    "campto": "Irinotecan",
    "camptosar": "Irinotecan",
    "hycamtin": "Topotecan",
    "gemzar": "Gemcitabine",
    "alimta": "Pemetrexed",
    "proleukin": "Aldesleukin",
    "interleukin-2": "Aldesleukin",
    "il-2": "Aldesleukin",
    "folic": "Folic Acid",
    "folinic acid": "Leucovorin",
    "leucovorin calcium": "Leucovorin",
    "zinecard": "Dexrazoxane",
    "mesnex": "Mesna",
    "elitek": "Rasburicase",
    "zyloprim": "Allopurinol",
    "exjade": "Deferasirox",
    "desferal": "Deferoxamine",
    "actigall": "Ursodiol",
    "cellcept": "Mycophenolate",
    "sandimmune": "Cyclosporine",
    "neoral": "Cyclosporine",
    "blenoxane": "Bleomycin",
    "bcnu": "Carmustine",
    "ccnu": "Lomustine",
    "myleran": "Busulfan",
    "dtic": "Dacarbazine",
    "temodar": "Temozolomide",
    "matulane": "Procarbazine",
    "trisenox": "Arsenic Trioxide",
    "thalomid": "Thalidomide",
    "vepesid": "Etoposide",
    "vp-16": "Etoposide",
    "novantrone": "Mitoxantrone",
    "fludara": "Fludarabine",
    "leustatin": "Cladribine",
    "2-cda": "Cladribine",
    "clolar": "Clofarabine",
    "arranon": "Nelarabine",
    "nipent": "Pentostatin",
    "mylotarg": "Gemtuzumab Ozogamicin",
    "campath": "Alemtuzumab",
    "tarceva": "Erlotinib",
    "sprycel": "Dasatinib",
    "tasigna": "Nilotinib",
    "nexavar": "Sorafenib",
    "afinitor": "Everolimus",
    "torisel": "Temsirolimus",
    "zolinza": "Vorinostat",
    "blincyto": "Blinatumomab",
    "unituxin": "Dinutuximab",
    "remicade": "Infliximab",
    "enbrel": "Etanercept",
    "zenapax": "Daclizumab",
    "soliris": "Eculizumab",
    "defitelio": "Defibrotide",
    "voraxaze": "Glucarpidase",
    "mozobil": "Plerixafor",
    "elspar": "Asparaginase",
    "erwinase": "Asparaginase",
    "oncaspar": "Asparaginase",
    "peg-asparaginase": "Asparaginase",
    "ontak": "Denileukin Diftitox",
    "intron": "Interferon",
    "roferon": "Interferon",
    "ethyol": "Amifostine",
    "cytovene": "Ganciclovir",
    "vistide": "Cidofovir",
    "foscavir": "Foscarnet",
    "mepron": "Atovaquone",
    "nebupent": "Pentamidine",
    "kytril": "Granisetron",
    "vistaril": "Hydroxyzine",
    "atarax": "Hydroxyzine",
    "neurontin": "Gabapentin",
    "accutane": "Isotretinoin",
    "toradol": "Ketorolac",
    "indocin": "Indomethacin",
    "inderal": "Propranolol",
    "lovenox": "Enoxaparin",
    "ddavp": "Desmopressin Acetate",
    "desmopressin": "Desmopressin Acetate",
    "amicar": "Aminocaproic Acid",
    "atg": "Antithymocyte Globulin",
    "thymoglobulin": "Antithymocyte Globulin",
    "winrho": "Rho(D) Immune Globulin",
    "factor viii": "Recombinant Factor VIII",
    "factor ix": "Recombinant Factor IX",
    "factor 8": "Recombinant Factor VIII",
    "factor 9": "Recombinant Factor IX",
    "doxil": "Liposomal Doxorubicin",
    "depocyt": "Liposomal Cytarabine",
    "ranitidine": "Histamine H2 Antagonist",
    "famotidine": "Histamine H2 Antagonist",
    "h2 blocker": "Histamine H2 Antagonist",
    "omeprazole": "Proton Pump Inhibitors",
    "pantoprazole": "Proton Pump Inhibitors",
    "ppi": "Proton Pump Inhibitors",
    "prilosec": "Proton Pump Inhibitors",
    "prevacid": "Proton Pump Inhibitors",
    "nystatin": "Nystatin/Clotrimazole",
    "clotrimazole": "Nystatin/Clotrimazole",
    "nitrogen mustard": "Mechlorethamine",
    "6-thioguanine": "Thioguanine",
    "liposomal doxorubicin": "Liposomal Doxorubicin",
    "liposomal cytarabine": "Liposomal Cytarabine",
    "liposomal amphotericin": "Liposomal Amphotericin B",
}

SEARCH_INDEX = {name.lower(): name for name in MEDICATION_INDEX}


def find_medication(query: str):
    q = query.strip().lower()
    if q in ALIASES:
        return ALIASES[q]
    if q in SEARCH_INDEX:
        return SEARCH_INDEX[q]
    matches = [name for key, name in SEARCH_INDEX.items() if q in key]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return min(matches, key=len)
    alias_matches = [canon for alias, canon in ALIASES.items() if q in alias]
    if alias_matches:
        return alias_matches[0]
    for name in MEDICATION_INDEX:
        if q in name.lower():
            return name
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    drug_list_json = json.dumps(sorted(MEDICATION_INDEX.keys()))
    return render_template_string(HTML_TEMPLATE, drug_list_json=drug_list_json)


@app.route("/api/medications")
def get_medications():
    return jsonify(sorted(MEDICATION_INDEX.keys()))


@app.route("/api/generate", methods=["POST"])
def generate_pdf():
    data = request.get_json(force=True)
    medications = data.get("medications", [])
    language = data.get("language", "en")

    if language not in ("en", "es"):
        return jsonify({"error": "Invalid language. Use 'en' or 'es'."}), 400
    if not medications:
        return jsonify({"error": "No medications specified."}), 400
    if not os.path.exists(SOURCE_PDF):
        return jsonify({"error": "Source PDF not found on server. Please add source.pdf."}), 500

    reader = PdfReader(SOURCE_PDF)
    writer = PdfWriter()
    found, not_found = [], []

    for med_query in medications:
        canon = find_medication(med_query)
        if canon and canon in MEDICATION_INDEX:
            for page_num in MEDICATION_INDEX[canon][language]:
                writer.add_page(reader.pages[page_num - 1])
            found.append(canon)
        else:
            not_found.append(med_query)

    if not found:
        return jsonify({"error": "None of the specified medications were found.", "not_found": not_found}), 404

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)

    lang_label = "Spanish" if language == "es" else "English"
    filename = f"APHON_Fact_Sheets_{lang_label}.pdf"

    response = send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)
    response.headers["X-Found"] = json.dumps(found)
    response.headers["X-Not-Found"] = json.dumps(not_found)
    response.headers["Access-Control-Expose-Headers"] = "X-Found, X-Not-Found"
    return response


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>APHON Fact Sheet Generator</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --navy: #0a1628;
    --navy-mid: #142040;
    --teal: #0ea5a0;
    --teal-light: #14c4be;
    --teal-dim: rgba(14,165,160,0.12);
    --teal-border: rgba(14,165,160,0.3);
    --text: #e8edf5;
    --text-muted: #7a8ba8;
    --text-dim: #4a5a72;
    --surface: rgba(255,255,255,0.04);
    --surface-hover: rgba(255,255,255,0.07);
    --border: rgba(255,255,255,0.08);
    --red: #f87171;
    --amber: #fbbf24;
    --green: #34d399;
  }

  html, body {
    min-height: 100vh;
    background: var(--navy);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
  }

  body {
    background-image:
      radial-gradient(ellipse 80% 50% at 50% -10%, rgba(14,165,160,0.15) 0%, transparent 60%),
      radial-gradient(ellipse 40% 30% at 90% 80%, rgba(10,100,160,0.1) 0%, transparent 50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 3rem 1rem 5rem;
  }

  /* ── Header ── */
  .site-header {
    width: 100%;
    max-width: 680px;
    text-align: center;
    margin-bottom: 2.5rem;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--teal-dim);
    border: 1px solid var(--teal-border);
    color: var(--teal-light);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    margin-bottom: 1.2rem;
  }

  h1 {
    font-size: clamp(1.6rem, 4vw, 2.4rem);
    font-weight: 700;
    line-height: 1.15;
    color: var(--text);
    letter-spacing: -0.02em;
    margin-bottom: 0.6rem;
  }

  h1 span { color: var(--teal-light); }

  .subtitle {
    font-size: 0.9rem;
    color: var(--text-muted);
    line-height: 1.5;
  }

  /* ── Card ── */
  .card {
    width: 100%;
    max-width: 680px;
    background: var(--navy-mid);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2rem;
    backdrop-filter: blur(12px);
  }

  /* ── Section label ── */
  .label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 0.65rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .section { margin-bottom: 1.5rem; }

  /* ── Language toggle ── */
  .lang-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
  }

  .lang-btn {
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--surface);
    color: var(--text-muted);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .lang-btn:hover { background: var(--surface-hover); color: var(--text); }

  .lang-btn.active {
    background: var(--teal-dim);
    border-color: var(--teal-border);
    color: var(--teal-light);
    font-weight: 600;
  }

  /* ── Search input ── */
  .input-row { display: flex; gap: 0.5rem; }

  .autocomplete-wrapper { position: relative; flex: 1; }

  input[type="text"] {
    width: 100%;
    padding: 0.75rem 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    outline: none;
    transition: border-color 0.15s;
  }

  input[type="text"]::placeholder { color: var(--text-dim); }
  input[type="text"]:focus { border-color: var(--teal-border); }

  /* ── Autocomplete ── */
  .ac-list {
    position: absolute;
    top: calc(100% + 4px);
    left: 0; right: 0;
    background: #1a2f50;
    border: 1px solid var(--teal-border);
    border-radius: 12px;
    max-height: 220px;
    overflow-y: auto;
    z-index: 200;
    display: none;
    box-shadow: 0 12px 32px rgba(0,0,0,0.4);
  }

  .ac-list.open { display: block; }

  .ac-list::-webkit-scrollbar { width: 4px; }
  .ac-list::-webkit-scrollbar-track { background: transparent; }
  .ac-list::-webkit-scrollbar-thumb { background: var(--teal-border); border-radius: 999px; }

  .ac-item {
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
    color: var(--text-muted);
    cursor: pointer;
    transition: background 0.1s;
    font-family: 'DM Mono', monospace;
  }

  .ac-item:hover, .ac-item.sel {
    background: var(--teal-dim);
    color: var(--teal-light);
  }

  .ac-item strong { color: var(--teal-light); font-weight: 700; }

  /* ── Add button ── */
  .btn-add {
    padding: 0.75rem 1.2rem;
    background: var(--teal);
    color: white;
    border: none;
    border-radius: 12px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;
    flex-shrink: 0;
  }

  .btn-add:hover { background: var(--teal-light); transform: translateY(-1px); }
  .btn-add:active { transform: none; }

  /* ── Tag list ── */
  .tag-area {
    min-height: 52px;
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    padding: 0.65rem;
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 12px;
    align-content: flex-start;
  }

  .empty-hint {
    color: var(--text-dim);
    font-size: 0.82rem;
    align-self: center;
    width: 100%;
    text-align: center;
    padding: 0.25rem 0;
  }

  .tag {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: var(--teal-dim);
    border: 1px solid var(--teal-border);
    color: var(--teal-light);
    padding: 0.3rem 0.6rem 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 500;
    animation: tagIn 0.15s ease;
  }

  @keyframes tagIn {
    from { opacity: 0; transform: scale(0.85); }
    to { opacity: 1; transform: scale(1); }
  }

  .tag-x {
    background: none;
    border: none;
    color: var(--teal-border);
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    transition: color 0.1s;
  }

  .tag-x:hover { color: var(--red); }

  .clear-btn {
    background: none;
    border: none;
    color: var(--text-dim);
    font-size: 0.72rem;
    font-family: 'DM Sans', sans-serif;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
    display: none;
  }

  .clear-btn:hover { color: var(--red); }

  .count-line {
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-top: 0.4rem;
    text-align: right;
    min-height: 1.1em;
    font-family: 'DM Mono', monospace;
  }

  /* ── Divider ── */
  .divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.5rem 0;
  }

  /* ── Generate button ── */
  .btn-gen {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, var(--teal) 0%, #0a8a86 100%);
    color: white;
    border: none;
    border-radius: 14px;
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    transition: all 0.15s ease;
    box-shadow: 0 4px 20px rgba(14,165,160,0.25);
    letter-spacing: -0.01em;
  }

  .btn-gen:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(14,165,160,0.35);
  }

  .btn-gen:active:not(:disabled) { transform: none; }

  .btn-gen:disabled {
    opacity: 0.35;
    cursor: not-allowed;
    box-shadow: none;
  }

  .spinner {
    width: 18px; height: 18px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: none;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Alert ── */
  .alert {
    margin-top: 1rem;
    padding: 0.85rem 1rem;
    border-radius: 10px;
    font-size: 0.85rem;
    line-height: 1.5;
    display: none;
  }

  .alert.show { display: block; }
  .alert-ok  { background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.25); color: #6ee7b7; }
  .alert-warn{ background: rgba(251,191,36,0.1);  border: 1px solid rgba(251,191,36,0.25);  color: #fcd34d; }
  .alert-err { background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.25); color: #fca5a5; }

  /* ── Footer ── */
  .footer {
    margin-top: 2rem;
    font-size: 0.75rem;
    color: var(--text-dim);
    text-align: center;
    line-height: 1.6;
  }
</style>
</head>
<body>

<header class="site-header">
  <div class="badge">
    <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
    APHON 5th Edition &nbsp;·&nbsp; 129 Medications
  </div>
  <h1>Medication <span>Fact Sheet</span> Generator</h1>
  <p class="subtitle">Select medications and patient language to generate a custom<br>PDF packet from the APHON Hematology/Oncology reference.</p>
</header>

<div class="card">

  <!-- Language -->
  <div class="section">
    <div class="label">Patient Language</div>
    <div class="lang-grid">
      <button class="lang-btn active" id="btn-en" onclick="setLang('en')">🇺🇸 English</button>
      <button class="lang-btn" id="btn-es" onclick="setLang('es')">🇪🇸 Español</button>
    </div>
  </div>

  <!-- Search -->
  <div class="section">
    <div class="label">Add Medications</div>
    <div class="input-row">
      <div class="autocomplete-wrapper">
        <input type="text" id="med-input"
               placeholder="Type a drug or brand name…"
               autocomplete="off"
               oninput="onInput()"
               onkeydown="onKey(event)" />
        <div class="ac-list" id="ac-list"></div>
      </div>
      <button class="btn-add" onclick="addMed()">+ Add</button>
    </div>
  </div>

  <!-- Tag area -->
  <div class="section">
    <div class="label">
      Selected Medications
      <button class="clear-btn" id="clear-btn" onclick="clearAll()">Clear all</button>
    </div>
    <div class="tag-area" id="tag-area">
      <span class="empty-hint" id="empty-hint">No medications added yet</span>
    </div>
    <div class="count-line" id="count-line"></div>
  </div>

  <hr class="divider">

  <!-- Generate -->
  <button class="btn-gen" id="gen-btn" onclick="generate()" disabled>
    <div class="spinner" id="spinner"></div>
    <svg id="dl-icon" width="18" height="18" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
    Generate &amp; Download PDF
  </button>

  <div class="alert" id="alert"></div>

</div>

<footer class="footer">
  Fact sheets sourced from APHON Hematology/Oncology Medication Fact Sheets, 5th Edition.<br>
  For healthcare professional use. Not a substitute for clinical judgment.
</footer>

<script>
const ALL_DRUGS = {{ drug_list_json }};
let selected = [], lang = 'en', acIdx = -1, acItems = [];

function setLang(l) {
  lang = l;
  document.getElementById('btn-en').classList.toggle('active', l === 'en');
  document.getElementById('btn-es').classList.toggle('active', l === 'es');
}

function onInput() {
  const q = document.getElementById('med-input').value.trim().toLowerCase();
  const list = document.getElementById('ac-list');
  acIdx = -1;
  if (!q) { list.classList.remove('open'); return; }
  acItems = ALL_DRUGS.filter(d => d.toLowerCase().includes(q)).slice(0, 9);
  if (!acItems.length) { list.classList.remove('open'); return; }
  list.innerHTML = acItems.map((d, i) =>
    `<div class="ac-item" data-i="${i}" onmousedown="pickAC('${d.replace(/'/g,"\\'").replace(/"/g,'&quot;')}',event)">${hl(d, q)}</div>`
  ).join('');
  list.classList.add('open');
}

function hl(text, q) {
  const i = text.toLowerCase().indexOf(q);
  if (i < 0) return text;
  return text.slice(0,i) + '<strong>' + text.slice(i, i+q.length) + '</strong>' + text.slice(i+q.length);
}

function pickAC(name, e) {
  e && e.preventDefault();
  document.getElementById('med-input').value = name;
  document.getElementById('ac-list').classList.remove('open');
  addMed();
}

function onKey(e) {
  const items = document.querySelectorAll('.ac-item');
  if (e.key === 'ArrowDown') { e.preventDefault(); acIdx = Math.min(acIdx+1, items.length-1); items.forEach((el,i)=>el.classList.toggle('sel',i===acIdx)); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); acIdx = Math.max(acIdx-1,-1); items.forEach((el,i)=>el.classList.toggle('sel',i===acIdx)); }
  else if (e.key === 'Enter') { e.preventDefault(); acIdx >= 0 && acItems[acIdx] ? pickAC(acItems[acIdx]) : addMed(); }
  else if (e.key === 'Escape') document.getElementById('ac-list').classList.remove('open');
}

document.addEventListener('click', e => {
  if (!e.target.closest('.autocomplete-wrapper'))
    document.getElementById('ac-list').classList.remove('open');
});

function addMed() {
  const inp = document.getElementById('med-input');
  const val = inp.value.trim();
  if (!val || selected.includes(val)) { inp.value=''; return; }
  selected.push(val);
  inp.value = '';
  document.getElementById('ac-list').classList.remove('open');
  render();
  inp.focus();
}

function removeMed(i) { selected.splice(i,1); render(); }
function clearAll() { selected=[]; render(); }

function render() {
  const area = document.getElementById('tag-area');
  const countLine = document.getElementById('count-line');
  const genBtn = document.getElementById('gen-btn');
  const clearBtn = document.getElementById('clear-btn');

  if (!selected.length) {
    area.innerHTML = '<span class="empty-hint">No medications added yet</span>';
    countLine.textContent = '';
    genBtn.disabled = true;
    clearBtn.style.display = 'none';
    return;
  }

  area.innerHTML = selected.map((m, i) =>
    `<span class="tag">${m}<button class="tag-x" onclick="removeMed(${i})" title="Remove">×</button></span>`
  ).join('');
  countLine.textContent = `${selected.length} medication${selected.length!==1?'s':''} selected`;
  genBtn.disabled = false;
  clearBtn.style.display = 'inline';
}

async function generate() {
  const btn = document.getElementById('gen-btn');
  const spinner = document.getElementById('spinner');
  const dlIcon = document.getElementById('dl-icon');
  const alert = document.getElementById('alert');

  btn.disabled = true;
  spinner.style.display = 'block';
  dlIcon.style.display = 'none';
  alert.className = 'alert';

  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ medications: selected, language: lang })
    });

    const found = JSON.parse(resp.headers.get('X-Found') || '[]');
    const notFound = JSON.parse(resp.headers.get('X-Not-Found') || '[]');

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || 'Generation failed');
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `APHON_Fact_Sheets_${lang === 'es' ? 'Spanish' : 'English'}.pdf`;
    a.click();
    URL.revokeObjectURL(url);

    const langName = lang === 'es' ? 'Spanish' : 'English';
    let msg = `✓ Downloaded ${found.length} fact sheet${found.length!==1?'s':''} in ${langName}.`;
    if (notFound.length) {
      msg += `<br>⚠ Not recognized: <em>${notFound.join(', ')}</em> — check spelling or try the generic name.`;
      alert.className = 'alert alert-warn show';
    } else {
      alert.className = 'alert alert-ok show';
    }
    alert.innerHTML = msg;

  } catch(err) {
    alert.className = 'alert alert-err show';
    alert.textContent = '✕ ' + err.message;
  } finally {
    btn.disabled = selected.length === 0;
    spinner.style.display = 'none';
    dlIcon.style.display = 'block';
  }
}
</script>
</body>
</html>"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
