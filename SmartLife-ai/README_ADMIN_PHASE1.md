# SmartLife AI — Administration, phase 1

Cette phase ajoute la séparation sécurisée entre les utilisateurs et l’administration.

## Modifications

- `utilisateurs.role` : `etudiant` ou `administrateur`
- `utilisateurs.matricule` : matricule étudiant, optionnel pour les comptes non étudiants
- `utilisateurs.statut` : `actif` ou `inactif`
- nouvelle route `/admin/`
- nouveau décorateur `@admin_required`
- nouveau blueprint `modules/admin.py`
- premier dashboard administratif

## Base de données existante

Exécuter une fois sur PostgreSQL :

```bash
psql "$DATABASE_URL" -f migration_admin_phase1.sql
```

Puis promouvoir le compte administratif avec son adresse réelle :

```sql
UPDATE utilisateurs
SET role = 'administrateur', statut = 'actif'
WHERE email = 'ADRESSE_ADMIN_REELLE';
```

## Important

La protection de `/admin/` relit le rôle et le statut en base à chaque requête administrative. Une ancienne session ne conserve donc pas un accès administrateur après une rétrogradation du compte.

La prochaine phase peut ajouter les filières, niveaux, matières, professeurs et préinscriptions.
