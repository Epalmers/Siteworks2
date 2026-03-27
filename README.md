# Siteworks

**Data Center Site Selection Dashboard**  
*CIVE-580: Applying AI in Environmental Engineering*

---

## What Is Siteworks?

Siteworks is a weighted multi-criteria decision analysis (MCDA) dashboard that helps non-engineer decision-makers evaluate whether a company should build a data center in a given city, based on water availability, climate, natural hazards, economics, and biodiversity factors.

It is designed to be **transparent, adjustable, and readable** — not a black-box.

> *"Is this site sustainable, or will it run out of water in 10 years?"*

---

## Why Does It Matter?

Data centers consume enormous amounts of water and energy.  Choosing the wrong location can lead to:

- Water supply shortfalls during droughts
- Higher cooling costs in hot, humid climates
- Operational shutdowns from natural disasters (floods, tornadoes)
- Regulatory and reputational risk in communities with environmental justice concerns

Siteworks puts these factors side by side so decision-makers can explore trade-offs quickly, before spending resources on detailed site investigations.

---

## Five Pilot Cities

| City | Key Characteristic |
|---|---|
| Oklahoma City, OK | Low electricity cost; high tornado risk |
| Boston, MA | Low cooling load; expensive electricity |
| Denver, CO | Dry climate; water stress; high altitude |
| Houston, TX | Very high flood risk; hot and humid |
| Gainesville, FL | High precipitation; wildlife constraints |

---

## How the Scoring Works

Siteworks implements a **Weighted MCDA** model as specified in the `CIVE580 Algorithms for AI.docx` document.

### Step 1 – Subcategory scores
Each city receives a score of **1–5** (5 = best) on 15 subcategory metrics:

| Category (default weight) | Subcategories |
|---|---|
| Hydrological & Regulatory Risk (25%) | Baseline Water Stress, Annual Precipitation, Recycled Water Infrastructure |
| Climate & Operational Physics (30%) | Cooling Degree Days, Annual Mean Humidity, Grid Carbon Intensity, Renewable Energy Mix |
| Economic & Social Impact (15%) | Industrial Electricity Rate, Water & Sewer Cost, Environmental Justice Index |
| Natural Hazards (20%) | Flood Risk, Tornado Frequency, Wildlife Hazard, Winter Weather Disruption |
| Biodiversity (10%) | Protected Area Proximity |

Note: some metrics are **scored inversely** — for example, high tornado frequency gives a low score.

### Step 2 – Category averages
Category score = average of its subcategory scores.

### Step 3 – Weighted total
```
Total = (Hydro × w₁) + (Climate × w₂) + (Economic × w₃) + (Hazards × w₄) + (Bio × w₅)
```
Weights are adjustable and always normalised to sum to 1.0.

### Step 4 – Ranking
Cities are sorted from highest total score (most suitable) to lowest.

---

## Source Files and Their Roles

| File | Role |
|---|---|
| `data/Data_Center_Site_Selector_RH.xlsx` | **Primary data source** — place here and the app will parse it automatically |
| `CIVE580 Algorithms for AI.docx` | Scoring logic specification (reference only) |
| `Project_Roadmap.docx` | Feature roadmap and product requirements |
| `CIVE 580 Project MAA.xlsx` | Future-expansion template; **not parsed** in this release |
| `Data-Center-Site-Selector-A-Vibe-Coding-Approach.pptx` | UX and product direction |
| `src/data/loader.py` | Built-in pilot dataset + Excel loader |
| `src/data/parser.py` | Excel workbook parser (documented assumptions inside) |
| `src/logic/scoring.py` | MCDA scoring engine |
| `src/logic/scenarios.py` | Weight presets and scenario modifiers |
| `src/logic/summaries.py` | Template-based natural language summaries |
| `src/ui/` | Streamlit chart, table, and layout components |
| `app.py` | Main Streamlit entry point |
| `tests/` | Pytest unit tests |

---

## How to Run the App Locally

### 1. Clone the repo
```bash
git clone https://github.com/Epalmers/Siteworks2.git
cd Siteworks2
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Add the Excel workbook
Place `Data_Center_Site_Selector_RH.xlsx` in the `/data/` folder.  
If the file is absent, the app uses its built-in pilot dataset.

### 4. Run the app
```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

### 5. Run the tests
```bash
pytest tests/ -v
```

---

## App Features

| Tab | What you can do |
|---|---|
| 📊 Rankings & Overview | See ranked table, bar charts, radar chart, and plain-language summary |
| 🆚 Compare Cities | Select two cities for side-by-side comparison with delta charts |
| 🔍 Data Explorer | Inspect subcategory scores and data sources per city |
| ℹ️ About & Methodology | Full methodology explanation and project background |

**Sidebar controls:**
- Adjust category weights with sliders (auto-normalised)
- Choose a named scenario preset (Water Stress, Carbon/Grid, Cost, Hazard)
- Toggle prototype what-if scenarios (Drought Year, 2050 Climate Shift)

---

## Project Architecture

```
app.py                  ← Streamlit entry point
src/
  data/
    schema.py           ← Normalized data model (dataclasses, constants)
    parser.py           ← Excel workbook parser (assumptions documented here)
    loader.py           ← Data loader + built-in pilot dataset
  logic/
    scoring.py          ← MCDA scoring engine
    validation.py       ← Weight and score validation helpers
    scenarios.py        ← Weight presets and scenario modifiers
    summaries.py        ← Template-based NLG summaries
  ui/
    sidebar.py          ← Sidebar controls
    charts.py           ← Plotly chart helpers
    tables.py           ← Ranked table rendering
    compare.py          ← Two-city comparison view
    explainers.py       ← Methodology explainers and data quality panel
data/                   ← Place Excel workbooks here
tests/
  test_scoring.py       ← Scoring engine unit tests
  test_validation.py    ← Validation unit tests
requirements.txt
README.md
```

---

## Current Limitations

- Pilot dataset covers only 5 cities.
- Scores are estimates based on publicly available data; site-specific measurements will differ.
- The Excel parser handles common workbook layouts but may need adjustments if the workbook structure changes significantly.
- Scenario modifiers (Drought Year, 2050 Climate Shift) apply approximate adjustments based on literature estimates, not full climate model runs.
- The `CIVE 580 Project MAA.xlsx` expansion workbook is not parsed in this release.

---

## Future Improvements

- Map integration (Folium or Mapbox) for geographic context
- Upload custom city data via the UI
- Full CMIP6 regional climate projections for 2050 scenario
- Sensitivity / Monte Carlo analysis for weight uncertainty
- AI-generated narrative summaries (optional LLM integration)
- PDF report export
- Additional cities beyond the 5-city pilot

---

## Acknowledgements

Built for **CIVE-580: Applying AI in Environmental Engineering**  
Colorado State University  
Project data and scoring logic from course materials.  
Public data sources: NOAA, EIA, WRI Aqueduct, FEMA, EPA EJScreen, NOAA SPC.
