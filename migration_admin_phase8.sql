CREATE TABLE IF NOT EXISTS annonces_academiques (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(180) NOT NULL,
    contenu TEXT NOT NULL,
    target_type VARCHAR(30) NOT NULL DEFAULT 'tous',
    target_id INTEGER,
    publie BOOLEAN NOT NULL DEFAULT TRUE,
    publie_le TIMESTAMP,
    auteur_id INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_annonces_academiques_created_at ON annonces_academiques(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_annonces_academiques_target ON annonces_academiques(target_type, target_id);

CREATE TABLE IF NOT EXISTS evenements_academiques (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(180) NOT NULL,
    description TEXT,
    type_evenement VARCHAR(40) NOT NULL DEFAULT 'autre',
    debut TIMESTAMP NOT NULL,
    fin TIMESTAMP,
    lieu VARCHAR(180),
    created_by_id INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_evenements_academiques_debut ON evenements_academiques(debut);
