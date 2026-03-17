# Whose Voices Shape Education Policy?
## Comparative Discourse Ecosystem Analysis: England, Ireland, Scotland
UCL Grand Challenges Project | Working Document

---

## 1. Comparative Source Table

The table below maps each organisation in the corpus to an equivalent functional slot across all three countries. Where a slot is absent in a given country, the cell is left empty. This is a structural map, not a claim about relative importance.

| Slot | England Org | England Type | Ireland Org | Ireland Type | Scotland Org | Scotland Type |
|---|---|---|---|---|---|---|
| Central govt | DfE | Government | Gov.ie | Government | Gov.scot | Government |
| Policy think tank | EPI | Education think tank | ESRI | Broad social research institute | SERA | Academic research assoc. |
| Foundation / funder | Nuffield Foundation | Private foundation | — | — | — | — |
| Data / research body | FFT Datalab | Independent data body | ERC | University research centre | — | — |
| Professional body | FED | Professional body | Teaching Council | Professional body | GTCS | Professional body |
| Professional body 2 | — | — | — | — | ADES | Professional assoc. (leaders) |
| Ed journalism | Schools Week | Specialist ed journalism | Education Matters | Specialist ed journalism | — | — |
| Advocacy / civil society | (not included) | — | (not included) | — | Children in Scotland | Advocacy body |

### Article counts and proportions

| Slot | England | % | Ireland | % | Scotland | % |
|---|---|---|---|---|---|---|
| Central govt | 699 | 18% | 799 | 77% | 201 | 38% |
| Policy think tank | 222 | 6% | 134 | 13% | 24 | 5% |
| Data / research body | 202 | 5% | 34 | 3% | 0 | 0% |
| Professional body | 104 | 3% | 36 | 3% | 119 | 23% |
| Ed journalism | 2,742 | 69% | 33 | 3% | 0 | 0% |
| Advocacy | 0 | 0% | 0 | 0% | 182 | 35% |
| **Total** | **3,943** | | **1,036** | | **526** | |

---

## 2. Notes on Comparability

Not all organisations filling the same slot are equivalent in form or function. Three distinctions matter:

### 2.1 Think tanks: form and policy orientation differ

All three countries have an organisation occupying the think tank functional slot, but the institutional type varies significantly:

- **England: EPI (+ Nuffield Foundation)** — EPI is a dedicated education policy think tank producing analysis directly aimed at influencing DfE policy. Nuffield is a private foundation funding education research. Both are part of a mature, well-resourced education policy ecosystem with direct lines to government.

- **Ireland: ESRI** — The Economic and Social Research Institute is a broad social research body covering economics, housing, health, and education. Education is one research area among many. Their education output is academically rigorous but less policy-prescriptive than EPI. The education content was extracted using ESRI's own topic filter (`?research_areas[]=63`).

- **Scotland: SERA** — The Scottish Educational Research Association is an academic membership body, not a policy think tank. Their output is conference proceedings, research summaries, and member communications rather than the policy briefs and rapid-response analyses that EPI produces. Only 24 articles in the corpus reflects this different function.

**Implication for analysis:** The "think tank" topic distribution will reflect different institutional functions across countries. England's think tank content is policy-oriented; Ireland's is broader social research; Scotland's is academic.

### 2.2 Professional bodies: scope and function differ

- **England: FED** — Foundation for Educational Development. School leadership focused.
- **Ireland: Teaching Council** — Statutory regulator for the teaching profession. Publishes regulatory updates, registration requirements, professional standards.
- **Scotland: GTCS + ADES** — GTCS is the statutory teaching regulator (equivalent to Teaching Council). ADES is a professional network for education directors/leaders (closer to FED). Scotland has two sources in this category.

### 2.3 Education journalism: the most significant structural difference

- **England** has Schools Week — a free, dedicated, high-volume education news outlet publishing multiple articles daily (~900/year). This creates a rich, publicly accessible critical media layer between government and the profession. Schools Week alone constitutes 69% of the England corpus.

- **Ireland** has Education Matters — a smaller specialist outlet (33 articles). TheJournal.ie had education coverage but became inaccessible due to a login wall during scraping. The Irish Times is fully paywalled. RTÉ keeps no archive.

- **Scotland** has no free dedicated education journalism outlet. TES Scotland is fully paywalled. The Herald and Scotsman are also paywalled.

**Implication for analysis:** England's topic model will be heavily shaped by journalistic framing — investigative reporting, editorial commentary, stakeholder reaction pieces. Ireland and Scotland's models will reflect institutional/governmental framing — press releases, policy announcements, research summaries. Cross-country JSD scores will partly measure this structural difference in **who speaks** about education policy, not just differences in **what they say**.

### 2.4 Advocacy: only Scotland has a dedicated source

Children in Scotland is an advocacy body representing children's rights and services organisations. Neither England nor Ireland has an equivalent in the current corpus (Children's Commissioner for England and Children's Rights Alliance for Ireland are on the future expansion list).

This means Scotland's corpus includes a civil society voice that England and Ireland lack. At 35% of the Scotland corpus, this is a significant framing influence.

---

## 3. Structural findings from the data collection process

### 3.1 The education media ecosystem differs fundamentally across jurisdictions

The data collection process itself revealed a key structural difference: **the degree to which education policy is publicly debated through independent media varies dramatically across the three countries**.

England has a mature, open education media ecosystem with Schools Week providing daily free coverage. Scotland and Ireland lack this entirely — their education discourse is mediated primarily through government communications, professional bodies, and (to a lesser extent) research organisations.

This is not a data collection limitation — it is a finding about the structure of education policy discourse in each jurisdiction.

### 3.2 Government dominance varies

| Country | Govt share of corpus |
|---|---|
| Ireland | 77% |
| Scotland | 38% |
| England | 18% |

Ireland's corpus is overwhelmingly governmental — the Department of Education's press releases and publications dominate. Scotland is more balanced between government and advocacy. England's government share is diluted by the volume of journalism.

### 3.3 Corpus size reflects real differences

| Country | Articles | Population | Articles per million people |
|---|---|---|---|
| England | 3,943 | 56m | 70 |
| Ireland | 1,036 | 5m | 207 |
| Scotland | 526 | 5.5m | 96 |

Per capita, Ireland actually produces more education policy content than England — but it is concentrated in government channels rather than distributed across media and civil society.

---

## 4. Methodological implications for NMF/BERTopic analysis

1. **JSD scores between countries will reflect both policy differences AND structural ecosystem differences.** This should be acknowledged in the analysis.

2. **Topic distributions will be shaped by source type.** England's topics will be more journalistic (framed as stories, controversies, reactions). Ireland's will be more governmental (framed as announcements, initiatives, statistics). Scotland's will mix government and advocacy framing.

3. **The language column allows sensitivity analysis.** A small number of Irish-language articles (3 flagged as `ga`) are retained in the corpus. Their influence on topic models can be tested by running with and without them.

4. **The title-only HE filter was applied consistently across all three countries** to remove articles clearly about higher education/universities. This was a light-touch filter (26 removed from England, 28 from Ireland) that preserves articles mentioning HE in passing while removing genuinely HE-focused content.

---

## 5. Future expansion sources

| Category | England | Ireland | Scotland |
|---|---|---|---|
| Advocacy | Children's Commissioner | Children's Rights Alliance | *(already included: Children in Scotland)* |
| Union | NEU | INTO | EIS |
| Parliament | Westminster Education Select Committee | Oireachtas | Scottish Parliament |

> Adding these would require retraining the NMF model. Deferred to a future iteration.
