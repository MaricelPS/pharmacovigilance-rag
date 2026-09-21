-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- Core tables: GLP-1 cohort (full detail)
-- ============================================================

CREATE TABLE IF NOT EXISTS reports (
    primaryid BIGINT PRIMARY KEY,
    caseid BIGINT NOT NULL,
    caseversion INT,
    event_dt DATE,
    fda_dt DATE,
    age NUMERIC,
    age_unit VARCHAR(20),
    sex VARCHAR(10),
    reporter_country VARCHAR(50),
    occur_country VARCHAR(50),
    reporter_type VARCHAR(20),
    serious BOOLEAN DEFAULT FALSE,
    faers_quarter VARCHAR(6) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_caseid ON reports(caseid);
CREATE INDEX IF NOT EXISTS idx_reports_age ON reports(age);
CREATE INDEX IF NOT EXISTS idx_reports_sex ON reports(sex);
CREATE INDEX IF NOT EXISTS idx_reports_quarter ON reports(faers_quarter);

CREATE TABLE IF NOT EXISTS drugs (
    id BIGSERIAL PRIMARY KEY,
    primaryid BIGINT NOT NULL REFERENCES reports(primaryid) ON DELETE CASCADE,
    drug_seq INT,
    role_cod VARCHAR(10),          -- PS: primary suspect, SS: secondary, C: concomitant, I: interacting
    drugname TEXT,
    prod_ai TEXT,                 -- Active ingredient
    route TEXT,
    dose_amt NUMERIC,
    dose_unit VARCHAR(50),
    is_glp1 BOOLEAN DEFAULT FALSE -- Flag for GLP-1 cohort membership
);

CREATE INDEX IF NOT EXISTS idx_drugs_primaryid ON drugs(primaryid);
CREATE INDEX IF NOT EXISTS idx_drugs_drugname_trgm ON drugs USING gin (drugname gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_drugs_prod_ai_trgm ON drugs USING gin (prod_ai gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_drugs_is_glp1 ON drugs(is_glp1) WHERE is_glp1 = TRUE;
CREATE INDEX IF NOT EXISTS idx_drugs_role ON drugs(role_cod);

CREATE TABLE IF NOT EXISTS reactions (
    id BIGSERIAL PRIMARY KEY,
    primaryid BIGINT NOT NULL REFERENCES reports(primaryid) ON DELETE CASCADE,
    pt TEXT NOT NULL,             -- MedDRA Preferred Term
    drug_rec_act TEXT
);

CREATE INDEX IF NOT EXISTS idx_reactions_primaryid ON reactions(primaryid);
CREATE INDEX IF NOT EXISTS idx_reactions_pt ON reactions(pt);
CREATE INDEX IF NOT EXISTS idx_reactions_pt_trgm ON reactions USING gin (pt gin_trgm_ops);

CREATE TABLE IF NOT EXISTS outcomes (
    id BIGSERIAL PRIMARY KEY,
    primaryid BIGINT NOT NULL REFERENCES reports(primaryid) ON DELETE CASCADE,
    outc_cod VARCHAR(10)           -- DE, LT, HO, DS, CA, RI, OT
);

CREATE INDEX IF NOT EXISTS idx_outcomes_primaryid ON outcomes(primaryid);
CREATE INDEX IF NOT EXISTS idx_outcomes_code ON outcomes(outc_cod);

CREATE TABLE IF NOT EXISTS indications (
    id BIGSERIAL PRIMARY KEY,
    primaryid BIGINT NOT NULL REFERENCES reports(primaryid) ON DELETE CASCADE,
    indi_drug_seq INT,
    indi_pt TEXT
);

CREATE INDEX IF NOT EXISTS idx_indications_primaryid ON indications(primaryid);

-- ============================================================
-- Background aggregates: full FAERS universe, no PII
-- Used to compute disproportionality metrics (PRR, ROR)
-- ============================================================

CREATE TABLE IF NOT EXISTS drug_event_counts (
    drug_key TEXT NOT NULL,       -- Normalized active ingredient
    event_pt TEXT NOT NULL,       -- MedDRA PT
    n_reports INT NOT NULL,       -- Reports mentioning both drug and event
    faers_quarter VARCHAR(6) NOT NULL,
    PRIMARY KEY (drug_key, event_pt, faers_quarter)
);

CREATE INDEX IF NOT EXISTS idx_dec_drug ON drug_event_counts(drug_key);
CREATE INDEX IF NOT EXISTS idx_dec_event ON drug_event_counts(event_pt);

CREATE TABLE IF NOT EXISTS drug_totals (
    drug_key TEXT NOT NULL,
    faers_quarter VARCHAR(6) NOT NULL,
    n_reports INT NOT NULL,       -- Total reports mentioning this drug
    PRIMARY KEY (drug_key, faers_quarter)
);

CREATE TABLE IF NOT EXISTS event_totals (
    event_pt TEXT NOT NULL,
    faers_quarter VARCHAR(6) NOT NULL,
    n_reports INT NOT NULL,       -- Total reports mentioning this event
    PRIMARY KEY (event_pt, faers_quarter)
);

CREATE TABLE IF NOT EXISTS quarter_totals (
    faers_quarter VARCHAR(6) PRIMARY KEY,
    n_reports INT NOT NULL        -- Total unique reports in the quarter
);

-- ============================================================
-- Reference: GLP-1 drug dictionary
-- ============================================================

CREATE TABLE IF NOT EXISTS glp1_drugs (
    active_ingredient TEXT PRIMARY KEY,
    brand_names TEXT[],           -- Common brand names for text matching
    indication_class TEXT         -- 'diabetes', 'obesity', 'both'
);

INSERT INTO glp1_drugs (active_ingredient, brand_names, indication_class) VALUES
    ('semaglutide',   ARRAY['ozempic','wegovy','rybelsus'],           'both'),
    ('liraglutide',   ARRAY['victoza','saxenda'],                     'both'),
    ('tirzepatide',   ARRAY['mounjaro','zepbound'],                   'both'),
    ('dulaglutide',   ARRAY['trulicity'],                             'diabetes'),
    ('exenatide',     ARRAY['byetta','bydureon'],                     'diabetes'),
    ('lixisenatide',  ARRAY['adlyxin','lyxumia','soliqua'],           'diabetes')
ON CONFLICT (active_ingredient) DO NOTHING;

-- ============================================================
-- Precomputed signal metrics for GLP-1 drugs
-- Replaces the need to store full drug_event_counts in production.
-- ============================================================

CREATE TABLE IF NOT EXISTS glp1_signals (
    drug_key TEXT NOT NULL,
    event_pt TEXT NOT NULL,
    a BIGINT NOT NULL,           -- Reports with drug AND event
    b BIGINT NOT NULL,           -- Reports with drug, no event
    c BIGINT NOT NULL,           -- Reports without drug, with event
    d BIGINT NOT NULL,           -- Reports without drug or event
    prr NUMERIC,
    prr_chi2 NUMERIC,
    ror NUMERIC,
    ror_ci_low NUMERIC,
    ror_ci_high NUMERIC,
    ic NUMERIC,
    ic_ci_low NUMERIC,
    is_signal_ema BOOLEAN,
    is_signal_bcpnn BOOLEAN,
    PRIMARY KEY (drug_key, event_pt)
);

CREATE INDEX IF NOT EXISTS idx_glp1_signals_drug ON glp1_signals(drug_key);
CREATE INDEX IF NOT EXISTS idx_glp1_signals_ema ON glp1_signals(is_signal_ema) WHERE is_signal_ema = TRUE;
CREATE INDEX IF NOT EXISTS idx_glp1_signals_ic ON glp1_signals(ic DESC);

-- ============================================================
-- Embeddings for semantic search over MedDRA PTs
-- ============================================================

CREATE TABLE IF NOT EXISTS pt_embeddings (
    pt TEXT PRIMARY KEY,
    embedding vector(1024)        -- Voyage AI voyage-3 uses 1024 dims
);

CREATE INDEX IF NOT EXISTS idx_pt_embeddings_hnsw
    ON pt_embeddings USING hnsw (embedding vector_cosine_ops);