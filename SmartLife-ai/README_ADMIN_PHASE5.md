# SmartLife AI — Administration Phase 5

## Nouveautés
- Synthèse semestrielle des résultats publiés.
- Moyenne pondérée par coefficient.
- Total des crédits et crédits validés.
- Nombre de matières validées.
- Règles de passage configurables par année académique.
- Option de compensation configurable.
- Publication du bulletin par l'administration.
- Consultation des bulletins uniquement par l'étudiant concerné.
- Export du bulletin en PDF.

## Migration
```bash
psql "$DATABASE_URL" -f migration_admin_phase5.sql
```

## Routes principales
- `/admin/bulletins`
- `/admin/bulletins/regles`
- `/dashboard/mes-bulletins`
- `/dashboard/bulletin/<id>/pdf`

## Vérification
La syntaxe Python des modules modifiés a été vérifiée avec `py_compile`.
Le test réel contre PostgreSQL doit être effectué dans l'environnement de déploiement.
