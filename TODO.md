# TODO - Python PubSub Scanner

## Bugs & Fixes

- [x] ~~Fix broken tests - mock should return `NamespacedItem` objects instead of strings~~
- [ ] Add validation for YAML color format in `get_namespaces_colors()` (ensure valid hex colors)

## Features en cours

### Integration de namespaces_colors

- [x] ~~**Integrer `namespaces_colors` du config dans le scanner**~~
    - ✅ Le `ConfigHelper` expose déjà `get_namespaces_colors()` (ligne 138-146)
    - ✅ Le scanner a un paramètre `colors` dans `__init__` et l'utilise maintenant depuis le config
    - ✅ Modifier `EventFlowScanner.from_config()` pour passer `config.get_namespaces_colors()` au constructeur
    - ✅ Ajouter un test unitaire pour vérifier l'intégration

### Amélioration de la configuration

- [x] ~~**Ajouter support pour `namespaces_shapes` dans le YAML**~~
    - ✅ Le scanner supporte déjà le paramètre `shapes` dans le constructeur
    - ✅ Ajouter `get_namespaces_shapes()` dans `ConfigHelper`
    - ✅ Passer les shapes depuis le config au scanner
    - ✅ Documenter les formes Graphviz disponibles dans README.md

- [x] ~~**Ajouter support pour `fontname` dans le config**~~
    - ✅ Le scanner accepte déjà `fontname` mais maintenant c'est aussi dans le config
    - ✅ Ajouter une clé optionnelle `graph_fontname` dans le YAML
    - ✅ Mettre à jour la documentation

## Nouvelles fonctionnalités

### Visualisation avancée

- [ ] **Générateur de thèmes de couleurs**
    - Créer un script helper pour générer automatiquement des palettes de couleurs harmonieuses
    - Support pour différents modes : colorblind-safe, dark mode, light mode
    - Export vers le format YAML attendu par la config

- [ ] **Graphiques filtrés par namespace**
    - Générer des graphiques séparés pour chaque namespace
    - Utile pour les grandes architectures avec beaucoup d'événements
    - Ajouter un nouveau type de graphique `"by-namespace"`

- [ ] **Export vers d'autres formats**
    - Support pour SVG, PNG (via Graphviz)
    - Support pour Mermaid.js (pour intégration dans documentation Markdown)
    - Support pour PlantUML

### Analyse et métriques

- [x] ~~**Détection d'anomalies**~~
    - ✅ Détecter les événements orphelins (jamais publiés ou jamais écoutés)
    - ✅ Détecter les cycles dans les dépendances d'événements
    - ✅ Détecter les agents isolés (ni publishers ni subscribers)
    - ✅ Intégration non-invasive dans le payload (nouvelle clé 'anomalies')
    - ✅ 9 tests unitaires + 1 test d'intégration
    - ✅ Mode append : pas de régression, compatible avec l'existant
    - [ ] Générer un rapport d'analyse avec recommandations (TODO futur)

- [ ] **Métriques de complexité**
    - Calculer le nombre moyen de subscribers par événement
    - Calculer le fan-out moyen des agents publishers
    - Identifier les "super agents" (trop de responsabilités)
    - Score de complexité global de l'architecture

- [ ] **Historique des changements**
    - Tracker l'évolution du graphique au fil du temps
    - Détecter les breaking changes (événements supprimés/renommés)
    - Générer un changelog automatique

### Intégration et monitoring

- [ ] **Support pour webhooks**
    - Notifier des services externes lors de changements détectés
    - Slack, Discord, Microsoft Teams integration
    - Support pour des webhooks génériques

- [ ] **Mode diff**
    - Comparer deux scans et générer un diff visuel
    - Utile pour code review et CI/CD
    - Intégration avec Git pour comparer branches

- [ ] **Health checks**
    - Endpoint `/health` pour monitoring de la santé du scanner
    - Métriques Prometheus
    - Support pour OpenTelemetry

### Documentation et développement

- [ ] **Documentation interactive**
    - Générer une page HTML interactive avec le graphique
    - Zoom, pan, filtres par namespace
    - Cliquer sur un noeud pour voir détails (fichier source, lignes de code)

- [ ] **Plugin system**
    - Permettre aux utilisateurs d'ajouter des analyseurs custom
    - Permettre des générateurs de graphiques custom
    - API claire pour les extensions

## Améliorations du code

### Refactoring

- [x] ~~**Séparer la génération de graphiques**~~
    - ✅ Extraire la logique DOT dans un module `graph_generators/`
    - ✅ Un fichier par type de graphique (complete, full-tree, etc.)
    - ✅ Facilite l'ajout de nouveaux types de graphiques
    - ✅ Architecture pluggable avec classe de base `GraphGenerator`
    - ✅ Fonction `get_generator()` pour instancier les générateurs
    - ✅ Fonction `register_generator()` pour ajouter des générateurs custom
    - ✅ 13 nouveaux tests pour valider les générateurs

- [ ] **Type hints complets**
    - Ajouter des type hints partout où ils manquent
    - Activer `disallow_untyped_defs = true` dans mypy config
    - Vérifier avec mypy --strict

- [ ] **Améliorer la gestion d'erreurs**
    - Créer des exceptions custom (ScannerException, ConfigException, etc.)
    - Meilleure propagation des erreurs avec contexte
    - Logging structuré (avec niveau DEBUG/INFO/WARNING/ERROR)

### Tests

- [ ] **Augmenter la couverture de tests**
    - Actuellement : tests de base pour scanner et config
    - Ajouter tests pour `analyze_event_flow.py` (parsing d'agents)
    - Ajouter tests pour `generate_hierarchical_tree.py`
    - Ajouter tests d'intégration end-to-end

- [ ] **Tests de performance**
    - Tester avec un grand nombre d'agents (100+, 1000+)
    - Benchmark du temps de scan
    - Optimiser si nécessaire (parallel processing?)

- [ ] **Tests de régression visuelle**
    - Snapshot testing pour les graphiques générés
    - Détecter les changements inattendus dans le DOT output

### Performance

- [ ] **Cache des résultats de scan**
    - Éviter de rescanner si aucun fichier n'a changé
    - Utiliser les timestamps ou hash de fichiers
    - Configurable via le YAML

- [ ] **Scan incrémental**
    - Ne scanner que les fichiers modifiés depuis le dernier scan
    - Très utile pour le mode continu avec grand codebase

- [ ] **Parallel processing**
    - Scanner les agents en parallèle (multiprocessing)
    - Accélération significative pour les gros projets

## DevOps et CI/CD

- [ ] **Action GitHub**
    - Créer une GitHub Action pour intégrer le scanner dans CI/CD
    - Fail le build si des anomalies sont détectées
    - Poster le graphique en tant que comment sur les PRs

- [ ] **Docker image**
    - Créer une image Docker officielle
    - Permet d'exécuter le scanner sans installation Python
    - Exemple docker-compose.yml pour démarrage rapide

- [ ] **Pre-commit hook**
    - Hook pour scanner avant chaque commit
    - Avertir si des breaking changes sont détectés
    - Optionnel, configurable

## Documentation

- [ ] **Tutoriels et exemples**
    - Exemple complet d'architecture event-driven
    - Tutorial : intégration dans un projet existant
    - Best practices pour organiser agents et events

- [ ] **Architecture Decision Records (ADR)**
    - Documenter les décisions importantes de design
    - Pourquoi NamespacedItem? Pourquoi DOT format?
    - Facilite la contribution

- [ ] **API Reference complète**
    - Documentation auto-générée depuis les docstrings
    - Utiliser Sphinx ou MkDocs
    - Publier sur ReadTheDocs

## Ideas & Explorations

- [ ] **Support pour d'autres langages**
    - TypeScript/JavaScript
    - Java/Kotlin
    - Go
    - Parser générique configurable par regex

- [ ] **Integration avec des frameworks**
    - Plugin pour FastAPI
    - Plugin pour Django
    - Plugin pour Spring Boot

- [ ] **Mode "live"**
    - Scanner qui monitore les changements en temps réel (watchdog)
    - Push automatique à chaque modification
    - WebSocket pour mise à jour en direct dans le frontend

- [ ] **AI-powered suggestions**
    - Utiliser un LLM pour suggérer des améliorations d'architecture
    - Détecter les anti-patterns
    - Générer de la documentation automatiquement
