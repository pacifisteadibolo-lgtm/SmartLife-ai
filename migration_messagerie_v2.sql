-- ============================================================
--  SmartLife AI — Migration : suppression/modification de message,
--  effacement de conversation (cote utilisateur, comme WhatsApp)
--  A exécuter APRES migration_messagerie.sql :
--  psql "$DATABASE_URL" -f migration_messagerie_v2.sql
-- ============================================================

ALTER TABLE messages_prives  ADD COLUMN IF NOT EXISTS supprime BOOLEAN DEFAULT FALSE;
ALTER TABLE messages_prives  ADD COLUMN IF NOT EXISTS modifie  BOOLEAN DEFAULT FALSE;
ALTER TABLE messages_groupes ADD COLUMN IF NOT EXISTS supprime BOOLEAN DEFAULT FALSE;
ALTER TABLE messages_groupes ADD COLUMN IF NOT EXISTS modifie  BOOLEAN DEFAULT FALSE;

-- Effacer une discussion n'efface rien chez l'autre personne (comme WhatsApp) :
-- on retient juste, PAR UTILISATEUR, à partir de quand il/elle ne veut plus voir
-- les anciens messages d'une conversation donnée.
CREATE TABLE IF NOT EXISTS effacements_conversation (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL,
    autre_id    INT,              -- rempli pour une conversation privee
    groupe_id   INT,              -- rempli pour un groupe
    efface_le   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (autre_id)  REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (groupe_id) REFERENCES groupes(id)      ON DELETE CASCADE,
    CHECK (
        (autre_id IS NOT NULL AND groupe_id IS NULL) OR
        (autre_id IS NULL AND groupe_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_effacement_prive  ON effacements_conversation(user_id, autre_id);
CREATE INDEX IF NOT EXISTS idx_effacement_groupe ON effacements_conversation(user_id, groupe_id);
