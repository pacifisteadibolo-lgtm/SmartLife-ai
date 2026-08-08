-- ============================================================
--  SmartLife AI — Migration : Messagerie (privé + groupes)
--  A exécuter APRES schema.sql, une seule fois :
--  psql "$DATABASE_URL" -f migration_messagerie.sql
-- ============================================================

-- ──────────────────────────────────────────
--  GROUPES
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS groupes (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(150) NOT NULL,
    description VARCHAR(255),
    photo       VARCHAR(255) DEFAULT 'default_groupe.png',
    createur_id INT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (createur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  MEMBRES DE GROUPE
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS groupe_membres (
    id         SERIAL PRIMARY KEY,
    groupe_id  INT NOT NULL,
    user_id    INT NOT NULL,
    role       VARCHAR(20) DEFAULT 'membre',   -- admin / membre
    joined_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (groupe_id, user_id),
    FOREIGN KEY (groupe_id) REFERENCES groupes(id)      ON DELETE CASCADE,
    FOREIGN KEY (user_id)   REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  MESSAGES DE GROUPE
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages_groupes (
    id         SERIAL PRIMARY KEY,
    groupe_id  INT NOT NULL,
    user_id    INT NOT NULL,
    contenu    TEXT,
    type       VARCHAR(20) DEFAULT 'texte',   -- texte / photo / video / fichier
    fichier_id INT,
    date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (groupe_id)  REFERENCES groupes(id)      ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (fichier_id) REFERENCES fichiers(id)     ON DELETE SET NULL
);

-- ──────────────────────────────────────────
--  Pièces jointes sur les messages privés
-- ──────────────────────────────────────────
ALTER TABLE messages_prives ADD COLUMN IF NOT EXISTS fichier_id INT REFERENCES fichiers(id) ON DELETE SET NULL;

-- Un fichier peut maintenant aussi être attaché à un message privé
ALTER TABLE fichiers ADD COLUMN IF NOT EXISTS msg_prive_id  INT REFERENCES messages_prives(id) ON DELETE SET NULL;
ALTER TABLE fichiers ADD COLUMN IF NOT EXISTS msg_groupe_id INT REFERENCES messages_groupes(id) ON DELETE SET NULL;

-- ──────────────────────────────────────────
--  Index utiles
-- ──────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_groupe_membres_user   ON groupe_membres(user_id);
CREATE INDEX IF NOT EXISTS idx_groupe_membres_groupe  ON groupe_membres(groupe_id);
CREATE INDEX IF NOT EXISTS idx_messages_groupes_gid   ON messages_groupes(groupe_id, date);
