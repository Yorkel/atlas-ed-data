# AtlasED — Dataset & Pipeline Summary
UCL Institute of Education | Updated 17 March 2026

---

## Primary dataset design (Option 2)

| | Training | Inference (historical) | Inference (live) |
|---|---|---|---|
| **England** | 1 Jan 2023 to 31 Dec 2025 *(reference distribution)* | Not applicable *(England trains; inference starts 2026)* | 1 Jan 2026 onwards — weekly, every Friday from 15 Jan 2026 |
| **Scotland** | None *(inference only by design)* | 1 Jan 2023 to 31 Dec 2025 *(full historical batch)* | 1 Jan 2026 onwards — weekly, every Friday from 15 Jan 2026 |
| **Ireland** | None *(inference only by design)* | 1 Jan 2023 to 31 Dec 2025 *(full historical batch)* | 1 Jan 2026 onwards — weekly, every Friday from 15 Jan 2026 |

> **Rationale:** NMF trained on England corpus only (K=30). Inference applied to Scottish and Irish documents using English model weights. This allows JSD and KL asymmetry to measure cross-national divergence from the English reference distribution.

> **Known gap:** 1--14 Jan 2026 not covered by batch or weekly pipeline. Documented in corpus notes.

---

## Inference files (compiled across all three countries)

| File | Coverage | Notes |
|---|---|---|
| **Ireland inference (historical)** | 1 Jan 2023 to 31 Dec 2025 | One-off batch. Complete. 1,036 articles after post-processing. |
| **Scotland inference (historical)** | 1 Jan 2023 to 31 Dec 2025 | Pending — scrapers not yet tested. |
| **Combined weekly inference (gap fill)** | 15 Jan 2026 to 13 March 2026 | All three countries. England done (weeks 1-9). Ireland/Scotland pending. |
| **Combined weekly inference (live)** | 20 March 2026 onwards | All three countries. Automated. Every Friday. |

---

## Implementation task list

| # | Phase | Task | Status | Detail |
|---|---|---|---|---|
| 1 | Data collection | England: backfill missing scrapes | **Done** | Weeks 1-9 (15 Jan → 13 Mar 2026). 17-29 articles/week. |
| 2 | Data collection | Ireland: batch scrape | **Done** | Jan 2023 to 31 Dec 2025. 1,036 articles after post-processing. |
| 3 | Data collection | Scotland: check scrapers, then batch scrape | Pending | Check all scrapers first. Jan 2023 to 31 Dec 2025. |
| 4 | Data collection | Ireland/Scotland: backfill weekly gap | Pending | 15 Jan 2026 to 13 March 2026. |
| 5 | Post-processing | Apply title-only HE filter to all datasets | **Done** | England training: 26 removed. England inference: 1 removed. Ireland: 28 removed. |
| 6 | Post-processing | Add language column to all datasets | **Done** | Ireland: 3 articles flagged as `ga` (Irish). England: all `en`. |
| 7 | Post-processing | Fix gov.ie migration dates | Pending | One-off. ~500 articles have 2025-04-11/12 instead of real dates. |
| 8 | Compile files | Scotland inference file | Pending | Jan 2023 to 31 Dec 2025. |
| 9 | Pipeline | Automated weekly inference (live) | Pending | All three countries, 20 March onwards. |

---

## Ireland — Final source list and article counts

### Historical batch: Jan 2023 → 31 Dec 2025

| Source | Category | Method | Raw articles | After post-processing | Notes |
|---|---|---|---|---|---|
| Gov.ie (Dept of Education) | 1. Government | HTML (search page) | 820 | 799 | Press releases + publications. Migration date issue (see below). |
| ESRI | 3. Think tank / research | HTML | 137 | 134 | Education-filtered news + publications. |
| Teaching Council | 6. Professional body | WP API | 36 | 36 | Admin/maintenance posts filtered during scraping. |
| ERC | 5. Data / research org | WP API | 42 | 34 | ~3 Irish language articles. Some empty text articles dropped. |
| Education Matters | 7. Ed journalism | WP API | 37 | 33 | All content types (yearbook, blog, news). |
| TheJournal.ie | 7. Ed journalism | HTML | 163 | **0** | Login wall blocks text extraction (see below). Kept in pipeline for weekly scrapes. |
| RTÉ News | 7. Ed journalism | HTML | 0 | 0 | All articles are from 2026 (after until_date). No archive. Useful for weekly scrapes only. |
| **Total** | | | **1,235** | **1,036** | |

### Post-processing steps applied (in order)

1. **Drop empty text** — removed 171 rows (mostly gov.ie pages that are PDF links, index pages, or landing pages without `<p>` content; plus all 163 TheJournal.ie articles which returned empty due to login wall)
2. **Title-only HE filter** — removed 28 articles where title contained higher education terms (e.g. "university", "higher education") AND title did NOT contain any school-level terms
3. **Language flagging** — added `language` column using Irish function word frequency (threshold: 8+ indicators = `ga`). 3 articles flagged as Irish. All articles kept.
4. **Deduplication** — 0 duplicates found

### Category distribution (after post-processing)

| # | Category | Ireland source(s) | Articles | % |
|---|---|---|---|---|
| 1 | Government | Gov.ie | 799 | 77% |
| 2 | Government agency | — | 0 | 0% |
| 3 | Think tank / research | ESRI | 134 | 13% |
| 4 | Think tank / research | — | 0 | 0% |
| 5 | Data / research org | ERC | 34 | 3% |
| 6 | Professional body | Teaching Council | 36 | 3% |
| 7 | Education journalism | Education Matters | 33 | 3% |
| | **Total** | | **1,036** | **100%** |

### Comparison with England

| Category | England (count) | England (%) | Ireland (count) | Ireland (%) |
|---|---|---|---|---|
| 1. Government | 699 | 18% | 799 | 77% |
| 3/4. Think tank | 222 | 6% | 134 | 13% |
| 5. Data / research | 202 | 5% | 34 | 3% |
| 6. Professional body | 104 | 3% | 36 | 3% |
| 7. Ed journalism | 2,742 | 69% | 33 | 3% |
| **Total** | **3,943** | | **1,036** | |

---

## Decisions log — Ireland scrapers

### Sources dropped

| Source | Reason | Date dropped |
|---|---|---|
| Irish Times | Almost entirely paywalled. 0 usable articles. | 16 Mar 2026 |
| TASC | Broad social policy think tank. Only 8 articles matched education. Not education-focused. | 16 Mar 2026 |
| NCSE | Only 26 articles. Too few to justify a separate source. | 16 Mar 2026 |
| Children's Rights Alliance | No matching category in England/Scotland. Moved to future expansion with Children's Commissioner (ENG) and Children in Scotland (SCO). | 16 Mar 2026 |
| NCCA | Cloudflare 403 blocks all automated access including robots.txt. Not scrapeable. | 16 Mar 2026 |

### TheJournal.ie — login wall issue

TheJournal.ie (`/education/news/`) was initially scrapeable and returned 163 articles with full text during testing on 16 March 2026. After hitting HTTP 429 rate limit errors during scraping, the site began serving a login/donation wall instead of article content. All 163 articles returned with empty text on subsequent runs.

**Decision:** Keep TheJournal.ie in the weekly pipeline. The login wall may be temporary (IP-based rate limiting). If articles start returning text in future weekly scrapes, they'll be included automatically. For the historical batch (Jan 2023 → Dec 2025), TheJournal.ie contributes 0 articles.

**Implication:** Ireland has effectively no education journalism in the historical dataset. Education Matters (33 articles) is the only ed_journalism source. This is a structural finding about the Irish education media landscape, not a data collection failure.

### Gov.ie — migration date issue

When gov.ie rebuilt their website in April 2025, all historical content was stamped with migration dates (2025-04-11 or 2025-04-12) instead of the original publish dates. This means:
- Articles from 2019-2024 show as `2025-04-11` or `2025-04-12` in the search listing
- The real "Published on:" date is available on each article page (e.g. "Published on: 16 March 2023")
- A one-off date-fix script will fetch real dates from each article page. This is slow (~500 HTTP requests) and will be run separately, not as part of the regular pipeline.
- Future weekly scrapes will not be affected (new articles have correct dates).

### Post-scrape filtering approach

**Title-only HE filter** (applied to all countries):
- Remove article only if the TITLE contains a higher education term AND the TITLE does NOT contain any school-level term
- HE terms: `university`, `universities`, `college fees`, `undergraduate`, `postgraduate`, `phd`, `doctoral`, `campus`, `tuition fees`, `higher education`, `third level`
- School terms: `school`, `teacher`, `pupil`, `primary`, `secondary`, `leaving cert`, `junior cycle`, `senior cycle`, `SNA`, `DEIS`, `curriculum`, etc.
- This approach was chosen after a score-based filter proved too aggressive (removed all 163 TheJournal.ie articles and 303 total)

**Rationale:** The sources are already pre-filtered for education content (gov.ie = Dept of Education, ESRI = education research area, TheJournal.ie = `/education/news/`). The title-only filter is a light touch that catches genuinely HE-only articles without destroying school articles that mention "college" in passing.

**Applied to England too** for consistency: removed 26 articles from training data (3,969 → 3,943) and 1 from inference.

### Language detection

Irish language articles are **flagged, not removed**. The `language` column uses Irish function word frequency:
- Common Irish function words checked: ` agus `, ` na `, ` ar `, ` tá `, ` bhí `, ` scoil `, ` oideachas `, etc.
- Threshold: 8+ matches = `ga` (Irish), otherwise `en`
- 3 articles flagged as `ga` in the Ireland dataset
- Future-proof: can be replaced with `langdetect` library for Scots Gaelic (`gd`) and Welsh (`cy`) if expanding to those jurisdictions

**Decision:** Keep Irish-language articles in the dataset. The presence of bilingual policy content is a legitimate finding about Ireland's education policy landscape. Flag in analysis rather than filtering out.

---

## Finding: education media landscape differences

A key finding from the scraper development process is that the **education media ecosystem differs fundamentally across the three jurisdictions**:

- **England** has Schools Week — a free, dedicated, high-volume education news outlet (~900 articles/year, 69% of the England dataset). This creates a rich, publicly accessible layer of education policy discourse between government and the profession.
- **Scotland** has no free equivalent. TES Scotland is fully paywalled. The Herald and The Scotsman are also paywalled. Education policy discourse is dominated by government press releases, professional bodies, and research organisations.
- **Ireland** is similar. The Irish Times is fully paywalled. TheJournal.ie covers education as part of general news but access is now restricted by a login wall. RTÉ provides only ~37 recent stories with no archive. Government press releases (gov.ie) dominate the dataset at 77%.

This means the **type of public discourse** is structurally different across countries. In England, there is an independent media layer critically interrogating policy in real time. In Scotland and Ireland, the public conversation is shaped primarily by institutional voices (government, professional bodies, researchers).

**Methodological implication:** Cross-country divergence scores (JSD, KL asymmetry) will partly capture this structural difference in **who speaks** about education policy, not just differences in **what they say**. England's topic model is heavily shaped by journalistic framing; Scotland and Ireland's models reflect institutional/governmental framing. This should be flagged in the analysis as a feature of the data, not a limitation.

---

## Scotland — sources and status

### Selected sources (6 → 5, TES Scotland dropped)

| # | Source | Category | Method | Status | Articles |
|---|---|---|---|---|---|
| 1 | Scottish Government | 1. Government | Search page HTML | **Tested** | 201 (168 news + 33 publications) |
| 2 | Education Scotland | 2. Gov agency | JS-rendered | **Dropped — JS-rendered, not scrapeable** | 0 |
| 3 | SERA | 3. Think tank / research | WP API | Tested: 27 articles (may have more with `per_page=10` fix) | ~27 |
| 4 | Audit Scotland | 5. Data / research org | HTML | Not yet tested | — |
| 5 | GTCS | 6. Professional body | HTML | Not yet tested | — |
| 6 | TES Scotland | 7. Ed journalism | HTML | **Dropped — fully paywalled** | 0 |

### Gov.scot scraper findings

**Approach changed:** Originally used sitemap (`/sitemap.xml`) which returned all 2,067 gov.scot news URLs across all topics (health, economy, justice, farming, education). Rewritten to use education-filtered search pages:
- News: `https://www.gov.scot/news/?cat=filter&topic=education&sort=date` (813 total, 168 in date range)
- Publications: `https://www.gov.scot/publications/?cat=filter&topic=education&sort=date` (filtered, ~33 in date range)

**Text extraction:** Gov.scot article pages use `<main>` tag for content, not `div.body-content` or `<article>`. Initial run returned 168 articles with empty text until this was fixed.

**Publications filtering:** Gov.scot publications section contains a large volume of administrative documents:
- FOI releases (~40% of publications)
- Committee/board meeting minutes (~20%)
- Equality impact assessments (~10%)
- Terms of reference documents

These are filtered out during scraping by title keyword matching. Remaining publications (~30%) are policy-relevant: strategy documents, guidance, evaluations, statistics, frameworks.

**Pagination bug:** Pages 1-13 of publications are all 2026-dated items. The FOI title filter was applied before the date check, so filtered items didn't count as `skipped_future`, causing the scraper to stop on page 8. Fixed by moving the date check before the FOI filter.

**Higher education content:** Gov.scot's education topic includes university/HE content (e.g. "University of Dundee Taskforce", "Boosting university spin-outs"). These will be removed by the title-only HE filter in run.py post-processing, consistent with Ireland and England.

**Education Scotland:** Dropped 17 March 2026. Both listing and article pages are JavaScript-rendered — the raw HTML contains no article content, only script tags. The `requests` library cannot execute JavaScript; browser automation (Selenium/Playwright) would be needed but adds complexity not justified for this source. Content is primarily curriculum improvement updates and professional learning rather than policy discourse. Could revisit if browser automation is added to the pipeline.

**TES Scotland:** Tested 17 March 2026. All articles returned as paywalled. Same pattern as Ireland — Scotland has no free dedicated education journalism outlet.

### Deferred sources (future expansion)

- Children in Scotland — advocacy
- ADES — government agency / professional body
- EIS — professional body / union

### Future expansion sources (all three countries)

**Advocacy (new category):**
- England: Children's Commissioner
- Scotland: Children in Scotland
- Ireland: Children's Rights Alliance

**Blocked sources:**
- COSLA (Convention of Scottish Local Authorities) — has education-filtered news (`Children and Young People` category) but Cloudflare 403 blocks all automated access. Same issue as NCCA in Ireland.

**Union (new category):**
- England: NEU (National Education Union)
- Scotland: EIS (Educational Institute of Scotland)
- Ireland: INTO (Irish National Teachers' Organisation)

**Parliament (new category):**
- England: Westminster / Education Select Committee
- Scotland: Scottish Parliament
- Ireland: Oireachtas

> **Note:** Adding unions and parliament sources would require retraining the NMF model. Deferred to a future iteration.

---

## Scraper design decisions

### WordPress API `per_page` bug
Many WordPress sites silently cap `per_page=100` to a lower number (10-20). When the scraper requests page 2 with date filters, the API returns 400 (looks like "no more pages") when there are actually more posts. **All WP API scrapers now use `per_page=10`** to avoid this. Affected: SERA, ERC, Teaching Council, Education Matters.

### Gov.ie scraper approach
The gov.ie scraper uses the search page HTML (not the sitemap, which only contains school inspection reports):
- Press releases: `https://www.gov.ie/en/search/?category=Press+release&organisation=Department+of+Education+and+Youth`
- Publications: `https://www.gov.ie/en/search/?category=Publication&organisation=Department+of+Education+and+Youth`
- Results are in plain HTML with `data-createdat` attribute and links. Parsed with BeautifulSoup + lxml.
- Pagination: `&page=2`, `&page=3`, etc. Stops when no new articles found on a page.
- Duplicate detection prevents infinite loops (same articles appeared on every page after page 105 in earlier versions).

### ESRI scraping approach
ESRI covers all policy areas. Rather than scraping all 88 pages of general news, we use ESRI's own filters:
- **News:** `https://www.esri.ie/news?keywords=education`
- **Publications:** `https://www.esri.ie/publications/browse?research_areas[]=63`
- ESRI article pages have no `<time>` tags — dates are plain text parsed with regex.

### RTÉ pagination
RTÉ's education section only keeps ~37 recent stories (by design — focus on breaking news). Pagination beyond page 2 returns the same sidebar links. The scraper stops after 2 consecutive pages with no new articles.

### Pipeline post-processing (in run.py)
All inference CSVs go through `_postprocess()` which:
1. Drops rows with empty text
2. Applies title-only HE filter
3. Flags language (Irish word frequency, threshold=8)
4. Deduplicates by URL

This runs automatically for all countries on every inference scrape.

---

## Data columns

All output CSVs have these columns:

| Column | Description |
|---|---|
| `url` | Article URL |
| `title` | Article title |
| `date` | Publish date (YYYY-MM-DD). Gov.ie migration dates pending fix. |
| `text` | Full article text |
| `source` | Source identifier (e.g. `gov_ie`, `esri`, `schoolsweek`) |
| `country` | Country code (`eng`, `sco`, `irl`) |
| `type` | Source category (`government`, `think_tank`, `ed_res_org`, `prof_body`, `ed_journalism`) |
| `institution_name` | Full institution name |
| `language` | ISO 639-1 language code (`en`, `ga`, `gd`, `cy`) |
