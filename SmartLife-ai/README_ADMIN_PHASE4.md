# SmartLife AI — Administration Phase 4

## Notes et résultats

Cette phase ajoute un moteur d'évaluation flexible :
- plusieurs composantes d'évaluation par matière ;
- poids différents par composante ;
- barèmes différents (`note_sur`) ;
- normalisation de chaque composante sur 20 ;
- moyenne pondérée finale sur 20 ;
- seuil de validation configurable par matière (10/20 par défaut) ;
- enregistrement des notes par étudiant ;
- publication des résultats ;
- consultation côté étudiant uniquement des résultats publiés de son inscription.

## Migration

```bash
psql "$DATABASE_URL" -f migration_admin_phase4.sql
```

À appliquer après les migrations des phases 1, 2 et 3.

## Exemple

Une matière peut avoir :
- Contrôle continu : poids 30, barème 20
- TP : poids 20, barème 20
- Examen final : poids 50, barème 100

Les trois notes sont ramenées sur 20 puis combinées selon leurs poids.

## Vérification

La syntaxe Python des modules modifiés a été vérifiée avec `py_compile` et `ast`. Une connexion réelle à PostgreSQL n'est pas disponible dans l'environnement de génération ; la migration doit donc être exécutée et testée sur la base de l'application.
