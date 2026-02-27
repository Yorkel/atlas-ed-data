# Supabase Schema — `articles` table

## SQL (create from scratch)

```sql
DROP TABLE IF EXISTS articles;

CREATE TABLE articles (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url                   TEXT UNIQUE NOT NULL,
  dataset_type          TEXT NOT NULL,
  title                 TEXT,
  article_date          DATE,
  article_text          TEXT,
  source                TEXT,
  country               TEXT,
  article_type          TEXT,
  institution_name      TEXT,
  week_number           INTEGER,
  week_start            DATE,
  week_end              DATE,
  preview               TEXT,
  election_period       TEXT,
  topic_num             INTEGER,
  dominant_topic        TEXT,
  dominant_topic_weight FLOAT8,
  topic_probabilities   JSONB,
  text_clean            TEXT,
  run_id                TEXT,
  sentiment_score       FLOAT8,
  sentiment_label       TEXT,
  contestability_score  FLOAT8,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
```

---

## Column reference

| Column | Why included |
|---|---|
| `id` | UUID primary key — best practice for stable row identity, needed for model pipeline to update specific rows |
| `url` | Unique constraint — deduplication key for upsert, also the article link shown in dashboard |
| `dataset_type` | Distinguishes `training` vs `inference` — dashboard filters on this |
| `title` | Article headline — displayed in dashboard cards |
| `article_date` | Publication date — used for timeline views and `election_period` calculation |
| `article_text` | Full article body — fed into the model |
| `source` | Publisher name (e.g. `schoolsweek`) — dashboard filtering by source |
| `country` | `england` / future: `scotland`, `ireland` — multi-country dashboard filtering |
| `article_type` | Article type (e.g. `gov_inst`, `think_tank`) — dashboard filtering |
| `institution_name` | Named institution — finer-grained filtering than `source` |
| `week_number` | Which inference week (1–52) — groups articles for per-week model runs |
| `week_start` | Monday of that week — date range display in dashboard |
| `week_end` | Friday of that week — date range display in dashboard |
| `preview` | First 300 chars of text — dashboard article cards load this instead of full text |
| `election_period` | `pre_election` / `post_election` relative to July 4 2024 GE — central to contestability analysis |
| `topic_num` | Integer topic index (0–29) — dashboard uses this for colour-coding, sorting, filtering |
| `dominant_topic` | Topic label as string (e.g. `"curriculum"`) — human-readable label shown in dashboard |
| `dominant_topic_weight` | Confidence score for the assigned topic — filter out low-confidence assignments |
| `topic_probabilities` | Full 30-topic weight vector as JSONB — used for detailed topic breakdown charts |
| `text_clean` | Preprocessed text that actually went into the model — evidence of preprocessing for writeup |
| `run_id` | Which model version produced the labels (e.g. `nmf_v1_2026-02`) — model versioning audit trail |
| `sentiment_score` | Numeric sentiment value — trend charts over time |
| `sentiment_label` | `positive` / `negative` / `neutral` — dashboard filtering |
| `contestability_score` | Score indicating how contested/controversial the topic is — core research contribution |
| `created_at` | Row insert timestamp — audit trail |

---

## When each column is populated

| Column | Seed time | FastAPI model | Sentiment pipeline | Contestability pipeline |
|---|---|---|---|---|
| `id` | ✅ auto | | | |
| `url` | ✅ | | | |
| `dataset_type` | ✅ | | | |
| `title` | ✅ | | | |
| `date` | ✅ | | | |
| `text` | ✅ | | | |
| `source` | ✅ | | | |
| `country` | ✅ | | | |
| `type` | ✅ | | | |
| `institution_name` | ✅ | | | |
| `week_number` | ✅ inference only | | | |
| `week_start` | ✅ inference only | | | |
| `week_end` | ✅ inference only | | | |
| `preview` | ✅ | | | |
| `election_period` | ✅ | | | |
| `topic_num` | | ✅ | | |
| `dominant_topic` | | ✅ | | |
| `dominant_topic_weight` | | ✅ | | |
| `topic_probabilities` | | ✅ | | |
| `text_clean` | | ✅ | | |
| `run_id` | | ✅ | | |
| `sentiment_score` | | | ✅ | |
| `sentiment_label` | | | ✅ | |
| `contestability_score` | | | | ✅ |
| `created_at` | ✅ auto | | | |

---

## Notes

- `dataset_type = 'training'` rows have `week_number`, `week_start`, `week_end` as NULL — these are not weekly inference batches
- `dataset_type = 'training'` rows have `institution_name` as NULL — not captured in training CSVs
- `election_period` is computed at seed time from `date`: `pre_election` if before 2024-07-04, `post_election` if on or after
- `preview` is computed at seed time as `text[:300]` — never updated after seeding
- All model columns (`topic_num` through `run_id`) remain NULL until the FastAPI model pipeline is connected (Step 4 in todo.md)
- RLS is enabled; service role key bypasses RLS for seeding — no explicit policies needed until dashboard is built
