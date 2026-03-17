# atlas-ed-data

Data collection pipeline for the **AtlasED** project — a cross-jurisdictional analysis of education policy discourse across England, Scotland and the Republic of Ireland.

This repo scrapes, cleans and structures education policy articles from government bodies, think tanks, research organisations, professional bodies and education media. The resulting corpus feeds the [AtlasED analysis pipeline](https://github.com/Yorkel/atlas-ed-pipeline) for NMF topic modelling, BERTopic clustering, and Jensen-Shannon divergence analysis.

UCL Grand Challenges Project | UCL Institute of Education | 2026

---

## Dataset summary

| Country | Sources | Articles (retro) | Articles (weekly) | Period |
|---|---|---|---|---|
| **England** | 6 | 3,943 | 207 (9 weeks) | Jan 2023 – Mar 2026 |
| **Ireland** | 5 | 1,036 | 64 (9 weeks) | Jan 2023 – Mar 2026 |
| **Scotland** | 5 | 511 | 107 (9 weeks) | Jan 2023 – Mar 2026 |
| **Total** | **16** | **5,490** | **378** | |

England is training data (NMF reference distribution). Scotland and Ireland are inference-only.

---

## Sources by country

| Category | England | Ireland | Scotland |
|---|---|---|---|
| Government | DfE | Gov.ie | Gov.scot |
| Think tank | EPI | ESRI | SERA |
| Funder | Nuffield Foundation | — | — |
| Research org | FFT Datalab | ERC | — |
| Professional body | FED | Teaching Council | GTCS, ADES |
| Ed media | Schools Week | Education Matters | — |
| Civil society | — | — | Children in Scotland |

See [docs/dataset_analysis.md](docs/dataset_analysis.md) for detailed comparability notes and structural findings.

---

## How to use

### Full retrospective scrape (one-off)

```bash
cd src
python run.py --country eng --until 2025-12-31    # England training data
python run.py --country irl --until 2025-12-31    # Ireland inference
python run.py --country sco --until 2025-12-31    # Scotland inference
```

### Weekly inference scrape

```bash
python run.py --country eng --since 2026-03-14 --until 2026-03-20 --week 10
python run.py --country irl --since 2026-03-14 --until 2026-03-20 --week 10
python run.py --country sco --since 2026-03-14 --until 2026-03-20 --week 10
```

### Post-processing (automatic)

All inference runs automatically apply:
1. **Empty text removal** — drops articles with no body text
2. **Title-only HE filter** — removes articles clearly about higher education (title contains "university" etc. with no school-level terms)
3. **Language flagging** — adds `language` column (Irish `ga`, Scots Gaelic `gd`, default `en`)
4. **Deduplication** — by URL

---

## Data schema

| Column | Description |
|---|---|
| `url` | Source article URL |
| `title` | Article title |
| `date` | Publication date (YYYY-MM-DD) |
| `text` | Full article body text |
| `source` | Source key (e.g. `gov_ie`, `schoolsweek`, `sera`) |
| `country` | Jurisdiction (`eng`, `sco`, `irl`) |
| `type` | Source category: `government`, `think_tank`, `funder`, `research_org`, `prof_body`, `ed_media`, `civil_society` |
| `institution_name` | Full institution name |
| `language` | ISO 639-1 code (`en`, `ga`, `gd`) |

---

## Project structure

```
src/
├── run.py                      # Pipeline entry point — all modes and countries
├── england/                    # England scrapers
│   ├── dfe.py                  # GOV.UK education (DfE)
│   ├── schoolsweek.py          # Schools Week
│   ├── epi.py                  # Education Policy Institute
│   ├── nuffield.py             # Nuffield Foundation
│   ├── fftlabs.py              # FFT Education Datalab
│   └── fed.py                  # Foundation for Educational Development
├── scotland/                   # Scotland scrapers
│   ├── gov_scot.py             # Scottish Government (news + publications)
│   ├── sera.py                 # SERA
│   ├── gtcs.py                 # GTCS
│   ├── ades.py                 # ADES
│   └── children_in_scotland.py # Children in Scotland
└── ireland/                    # Ireland scrapers
    ├── gov_ie.py               # Dept of Education (gov.ie)
    ├── esri.py                 # ESRI
    ├── erc.py                  # Educational Research Centre
    ├── teaching_council.py     # Teaching Council
    ├── education_matters.py    # Education Matters
    ├── thejournal.py           # TheJournal.ie (login-walled, 0 articles currently)
    └── rte.py                  # RTÉ News (no archive, weekly only)

data/                           # Not in repo — regenerate by running scrapers
├── training/england/           # England training corpus (Jan 2023 – Dec 2025)
└── inference/
    ├── england/                # Weekly CSVs from Jan 2026
    ├── ireland/                # Retro (2025-12-31.csv) + weekly CSVs
    └── scotland/               # Retro (2025-12-31.csv) + weekly CSVs

docs/
├── scot_ire_dataset.md         # Full pipeline and dataset documentation
└── dataset_analysis.md         # Comparative discourse ecosystem analysis
```

---

## Key findings from data collection

The data collection process itself revealed structural differences in how education policy is publicly debated across the three jurisdictions:

- **England** has a mature, open education media ecosystem (Schools Week = 69% of corpus)
- **Scotland and Ireland** lack free dedicated education journalism — discourse is dominated by government and institutional voices
- **Government share:** Ireland 77%, Scotland 37%, England 18%

These differences are not data collection limitations — they are findings about the structure of education policy discourse. See [docs/dataset_analysis.md](docs/dataset_analysis.md).

---

## Adding a new source

1. Write scraper in `src/<country>/sourcename.py` with standard interface:
```python
def scrape_sourcename(since_date=None, until_date=None, output_path=None, append=False):
    return all_articles  # list of dicts with url, title, date, text
```

2. Register in `src/run.py` — add to `SCRAPERS`, `SOURCE_META`

3. Run: `python run.py --country <code> --until 2025-12-31`

---

## Installation

```bash
pip install -r requirements.txt
```

Dependencies: `requests`, `beautifulsoup4`, `lxml`, `pandas`, `langdetect`

---

## Future expansion

| Category | England | Ireland | Scotland |
|---|---|---|---|
| Union | NEU | INTO | EIS |
| Parliament | Westminster Ed Select Committee | Oireachtas | Scottish Parliament |
| Advocacy | Children's Commissioner | Children's Rights Alliance | *(included)* |

Adding these would require retraining the NMF model.

---

## Related

- **AtlasED analysis pipeline** — NMF, BERTopic, JSD analysis on this corpus (separate repo)
