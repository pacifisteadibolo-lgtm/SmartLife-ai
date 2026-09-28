# SmartLife AI — Administration Phase 7

## Comptes et permissions

Cette phase finalise la séparation des rôles :
- `etudiant` → espace SmartLife étudiant
- `professeur` → espace professeur
- `administrateur` → espace administration

### Migration
```bash
psql "$DATABASE_URL" -f migration_admin_phase7.sql
```

### Nouveautés
- redirection automatique après connexion selon le rôle ;
- création d'un compte professeur depuis l'administration ;
- activation du compte via lien temporaire ;
- changement obligatoire du mot de passe après activation ;
- activation/désactivation des comptes ;
- suivi de la dernière connexion ;
- page d'administration des comptes ;
- protection serveur des espaces par rôle et statut.

Le mot de passe temporaire n'est jamais affiché ni envoyé : le professeur choisit son propre mot de passe via le lien d'activation.
