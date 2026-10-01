ALTER TABLE matieres ADD COLUMN IF NOT EXISTS seuil_validation NUMERIC(5,2) NOT NULL DEFAULT 10;
CREATE TABLE IF NOT EXISTS evaluation_types (
    id SERIAL PRIMARY KEY,
    matiere_id INTEGER NOT NULL REFERENCES matieres(id) ON DELETE CASCADE,
    nom VARCHAR(100) NOT NULL,
    poids NUMERIC(6,2) NOT NULL DEFAULT 1,
    note_sur NUMERIC(6,2) NOT NULL DEFAULT 20,
    ordre INTEGER NOT NULL DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_evaluation_poids_positif CHECK (poids > 0),
    CONSTRAINT ck_evaluation_note_sur_positif CHECK (note_sur > 0)
);
CREATE INDEX IF NOT EXISTS idx_evaluation_types_matiere ON evaluation_types(matiere_id);

CREATE TABLE IF NOT EXISTS notes_evaluations (
    id SERIAL PRIMARY KEY,
    inscription_id INTEGER NOT NULL REFERENCES inscriptions_etudiants(id) ON DELETE CASCADE,
    evaluation_type_id INTEGER NOT NULL REFERENCES evaluation_types(id) ON DELETE CASCADE,
    note NUMERIC(6,2) NOT NULL,
    commentaire TEXT,
    saisi_par_id INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_note_etudiant_evaluation UNIQUE (inscription_id, evaluation_type_id)
);
CREATE INDEX IF NOT EXISTS idx_notes_inscription ON notes_evaluations(inscription_id);
CREATE INDEX IF NOT EXISTS idx_notes_evaluation_type ON notes_evaluations(evaluation_type_id);

CREATE TABLE IF NOT EXISTS resultats_matieres (
    id SERIAL PRIMARY KEY,
    inscription_id INTEGER NOT NULL REFERENCES inscriptions_etudiants(id) ON DELETE CASCADE,
    matiere_id INTEGER NOT NULL REFERENCES matieres(id) ON DELETE CASCADE,
    semestre_id INTEGER NOT NULL REFERENCES semestres(id) ON DELETE RESTRICT,
    note_finale NUMERIC(6,2) NOT NULL DEFAULT 0,
    moyenne_sur NUMERIC(6,2) NOT NULL DEFAULT 20,
    valide BOOLEAN NOT NULL DEFAULT FALSE,
    publie BOOLEAN NOT NULL DEFAULT FALSE,
    publie_le TIMESTAMP,
    commentaire TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_resultat_etudiant_matiere UNIQUE (inscription_id, matiere_id)
);
CREATE INDEX IF NOT EXISTS idx_resultats_inscription ON resultats_matieres(inscription_id);
CREATE INDEX IF NOT EXISTS idx_resultats_matiere ON resultats_matieres(matiere_id);
CREATE INDEX IF NOT EXISTS idx_resultats_publie ON resultats_matieres(publie);
