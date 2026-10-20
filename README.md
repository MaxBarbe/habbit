# Habbit ✦

**Un dressing intelligent pour composer ses tenues à partir de ses propres vêtements.**

[Présentation](https://maxbarbe.github.io/habbit/) · [Versions](https://github.com/MaxBarbe/habbit/releases) · [Historique](CHANGELOG.md)

## Le projet

Habbit est un prototype Python qui rassemble un dressing numérique, l’analyse de vêtements et des recommandations de tenues selon le contexte. Cette première publication est issue de **APP-HABIT-MEN** ; les variantes APP-Habit et APP-HABITv2 restent dans les dossiers locaux d’origine.

- Import de photos de vêtements et détourage via un moteur BiRefNet/Candle externe.
- Reconnaissance avec Marqo FashionCLIP ; estimation des couleurs, matières, saisons et styles.
- Dressing enregistré dans SQLite pour conserver les analyses.
- Suggestions de tenues tenant compte du style et de la météo via Open-Meteo.
- Essayage virtuel avec un serveur FASHN VTON local, si ses modèles sont installés.
- Interface Streamlit et API FastAPI.

## État : 0.1.0 — prototype

La page GitHub Pages présente le projet. Elle n’exécute pas l’application Python ni les modèles IA. Le traitement complet nécessite une installation locale et les moteurs décrits ci-dessous. Les prédictions IA restent des estimations.

## Installation locale

La variante source utilise Python 3.13 sur Mac Apple Silicon. Les versions Python sont consignées dans `requirements.txt`, à partir des métadonnées de son environnement local ; une installation propre et une validation IA complète restent à effectuer.

```bash
git clone https://github.com/MaxBarbe/habbit.git
cd habbit
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La base SQLite vide est créée au démarrage. Les photos, bases existantes, environnements virtuels et poids IA sont exclus du dépôt.

### Moteurs IA

**Reconnaissance :** FashionCLIP télécharge `Marqo/marqo-fashionCLIP` au premier chargement ; prévoir une connexion et de l’espace disque.

**Détourage :** fournir le binaire BiRefNet/Candle `infer_stream` et ses ressources. Ce moteur n’est pas distribué ici. Configurer son chemin avant le lancement :

```bash
export HABBIT_CANDLE_ENGINE="/chemin/vers/infer_stream"
```

Sans ce moteur, l’analyse des nouvelles photos ne peut pas fonctionner.

**Essayage virtuel (facultatif) :** le code de FASHN VTON et son adaptateur local sont dans `engines/fashn-vton`. Consulter son [README](engines/fashn-vton/README.md) pour les poids et prérequis, puis :

```bash
python -m pip install -e engines/fashn-vton
python -m uvicorn fashn_server:app --app-dir engines/fashn-vton --host 127.0.0.1 --port 8765
```

L’adaptateur utilise le périphérique Apple `mps`. Ajouter localement sa photo de référence dans `backend/storage/person/reference.png`. Les poids doivent être dans `engines/fashn-vton/weights/`. L’essayage reste indisponible sans serveur et modèles fonctionnels.

### API locale

```bash
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Documentation interactive : `http://127.0.0.1:8000/docs`.

## Organisation

| Dossier | Rôle |
| --- | --- |
| `app.py`, `ui/` | Interface Streamlit |
| `backend/api/` | API FastAPI |
| `backend/services/` | Analyse, contexte, recommandations, essayage |
| `backend/database/` | Persistance SQLite |
| `engines/fashn-vton/` | Moteur tiers et adaptateur local |
| `docs/` | Présentation publique GitHub Pages |

## Publier une nouvelle version

1. Modifier `VERSION` et `CHANGELOG.md` ; l’API lit automatiquement `VERSION`.
2. Vérifier le code puis pousser les changements sur `main`.
3. Créer et pousser le tag correspondant, par exemple `v0.1.1`.

Le workflow Release vérifie la cohérence du tag, lance un contrôle de syntaxe et crée une publication GitHub avec notes automatiques. Chaque mise à jour de `main` déploie la présentation. Les dépendances bénéficient de propositions mensuelles Dependabot ; elles doivent être testées avant intégration.

## Composants tiers

Le code FASHN VTON conserve sa licence Apache-2.0 dans son dossier. Les conditions des modèles téléchargés et des autres moteurs s’appliquent séparément. Aucune licence globale n’a été attribuée au code Habbit dans cette publication.
