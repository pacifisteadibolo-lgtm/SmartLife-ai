# SmartLife AI — Administration Phase 2

Cette version ajoute la structure académique à la Phase 1 d'administration.

## Fonctionnalités ajoutées

- Années académiques avec une seule année active.
- Filières.
- Niveaux rattachés à une filière et une année.
- Semestres.
- Professeurs.
- Matières rattachées à un niveau, un semestre et éventuellement un professeur.
- Coefficient et crédits pour chaque matière.
- Interface d'administration protégée par `admin_required`.

## Migration PostgreSQL

Après la migration de la Phase 1, exécuter :

```bash
psql "$DATABASE_URL" -f migration_admin_phase2.sql
```

L'utilisateur PostgreSQL utilisé par l'application doit avoir les droits de création/modification des tables.

## Accès

Une fois connecté avec un compte dont `role='administrateur'` et `statut='actif'` :

- `/admin/`
- `/admin/annees`
- `/admin/filieres`
- `/admin/niveaux`
- `/admin/semestres`
- `/admin/professeurs`
- `/admin/matieres`

Les comptes étudiants n'ont pas accès à ces routes.

## Suite prévue

La prochaine phase pourra ajouter :

1. gestion complète des étudiants (ajout, modification, activation/désactivation) ;
2. préinscriptions en ligne ;
3. admissions et génération de matricules ;
4. inscriptions académiques ;
5. méthodes d'évaluation et notes ;
6. calcul automatique des notes finales ;
7. espace étudiant « Mes notes / Mes résultats ».

## Vérification

Les fichiers Python de cette phase ont été vérifiés par compilation AST/py_compile. L'environnement de travail utilisé pour cette vérification ne contient pas les dépendances Python du projet (`flask_sqlalchemy` notamment), donc un lancement Flask complet n'a pas été effectué localement ici.
