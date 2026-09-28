CREATE TABLE IF NOT EXISTS regles_passage (
    id SERIAL PRIMARY KEY,
    annee_academique_id INTEGER NOT NULL UNIQUE REFERENCES annees_academiques(id) ON DELETE CASCADE,
    moyenne_min NUMERIC(5,2) NOT NULL DEFAULT 10,
    credits_min NUMERIC(6,2) NOT NULL DEFAULT 0,
    compensation_autorisee BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bulletins_semestres (
    id SERIAL PRIMARY KEY,
    inscription_id INTEGER NOT NULL REFERENCES inscriptions_etudiants(id) ON DELETE CASCADE,
    semestre_id INTEGER NOT NULL REFERENCES semestres(id) ON DELETE RESTRICT,
    moyenne NUMERIC(6,2) NOT NULL DEFAULT 0,
    total_credits NUMERIC(7,2) NOT NULL DEFAULT 0,
    credits_valides NUMERIC(7,2) NOT NULL DEFAULT 0,
    matieres_validees INTEGER NOT NULL DEFAULT 0,
    matieres_total INTEGER NOT NULL DEFAULT 0,
    publie BOOLEAN NOT NULL DEFAULT FALSE,
    decision VARCHAR(40) NOT NULL DEFAULT 'En cours',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_bulletin_inscription_semestre UNIQUE (inscription_id, semestre_id)
);

CREATE INDEX IF NOT EXISTS idx_bulletins_inscription ON bulletins_semestres(inscription_id);
CREATE INDEX IF NOT EXISTS idx_bulletins_semestre ON bulletins_semestres(semestre_id);
CREATE INDEX IF NOT EXISTS idx_bulletins_publie ON bulletins_semestres(publie);
