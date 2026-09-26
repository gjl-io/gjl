# gjl

**Une frontière de politiques auto-hébergée pour le trafic LLM.**

Inspectez les requêtes sortantes, bloquez le contenu sensible ou réécrivez les corps de requêtes décodés à l'aide de règles d'expressions régulières ordonnées, et contrôlez les identifiants de fournisseur au niveau d'une frontière que vous exploitez.

[English](README.md) · [한국어](README.ko.md) · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md)

[Site Web](https://gjl.io/) · [Versions](https://github.com/gjl-io/gjl/releases) ·
[Installation et vérification](docs/install.md) · [Rapports de sécurité](SECURITY.md) ·
[Accès distant](docs/remote-exposure.md) ·
[Observateur de connexions](docs/connection-observer.md) ·
[Licences](LICENSE.md)

## Installation rapide et prise en main

Installez gjl avec une seule commande. Le programme d'installation détecte automatiquement votre système d'exploitation, l'architecture de votre processeur et votre environnement graphique, configure votre variable `PATH` et met en place les composants appropriés.

### Windows (PowerShell)

```powershell
irm https://gjl.io/install.ps1 | iex
```

*Ou via `curl.exe` :*
```powershell
curl.exe -fsSL https://gjl.io/install.ps1 | powershell -Command -
```

### macOS et Linux (curl)

```bash
curl -fsSL https://gjl.io/install.sh | sh
```

### Installation CLI uniquement (sans l'interface Desktop)

Si vous préférez installer uniquement la CLI autonome `gjl` sur un système doté d'un environnement de bureau graphique :

* **Windows :**
  ```powershell
  $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
  # ou : & ([scriptblock]::Create((irm https://gjl.io/install.ps1))) -CliOnly
  ```
* **macOS et Linux :**
  ```bash
  curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
  # ou : curl -fsSL https://gjl.io/install.sh | GJL_CLI_ONLY=1 sh
  ```

> [!TIP]
> **Environnements sans affichage (Headless) et serveurs** : Sur les systèmes sans serveur d'affichage (tels que les serveurs Linux, les sessions SSH headless ou Windows Server Core), le programme d'installation ignore automatiquement le téléchargement de Flutter Desktop et installe uniquement la CLI autonome `gjl`.

### Exécution

Immédiatement après l'installation dans votre terminal actuel :

- **Desktop GUI :**
  ```bash
  gjl gui
  ```
- **Terminal / Sans affichage (Headless) :**
  ```bash
  gjl run
  ```

### Mise à jour de gjl

Maintenez votre installation à jour avec `gjl update` :

```bash
gjl update             # Mettre à jour tous les composants installés localement (CLI et/ou Desktop)
gjl update --cli-only  # Mettre à jour uniquement la CLI gjl
gjl update --gui-only  # Mettre à jour uniquement l'interface Desktop
gjl update --dry-run   # Vérifier les mises à jour sans les télécharger
```

Pour les téléchargements manuels de binaires et la vérification des sommes de contrôle, consultez [Installer et vérifier gjl](docs/install.md).

## À qui s'adresse gjl

- **Personnes et équipes soucieuses de la sécurité** qui souhaitent bloquer ou masquer du contenu sensible avant qu'il n'atteigne un fournisseur, conserver les identifiants de fournisseur dans une limite qu'elles contrôlent et, éventuellement, enregistrer les requêtes LLM ainsi que des copies de réponses assainies dans des journaux locaux.
- **Utilisateurs en quête de meilleurs résultats LLM** qui utilisent des règles de route pour adapter le libellé des invites ou sélectionner un autre modèle pris en charge par le fournisseur dans les requêtes inspectables, selon les besoins d'un flux de travail donné.
- **Individus ou organisations disposant de plusieurs comptes auprès d'un même fournisseur LLM** souhaitant une route distincte pour chaque identifiant et un contrôle explicite du compte utilisé par chaque client. gjl n'effectue aucun équilibrage de charge ni basculement automatique entre les comptes.
- **Développeurs et équipes utilisant plusieurs outils d'agents de code** qui souhaitent suivre la consommation de jetons (tokens), calculer les coûts estimés et comparer les habitudes d'utilisation entre différents agents ou flux de travail.
- **Responsables d'équipe et organisations** souhaitant consolider la consommation de jetons et les coûts estimés par collaborateur, identité de client ou identifiant sur une infrastructure partagée.

## Ce que fait gjl

gjl s'exécute entre un client LLM (comme un agent de code, une extension d'EDI ou un outil de développement) et un fournisseur LLM. Chaque route appartient soit à Door, soit à Gate, et détient sa propre cible de fournisseur, source d'identifiants, politique d'authentification entrante et règles de masquage.

Le cheminement protégé d'une requête est le suivant :

```text
corps décodé
  → vérification préalable des règles de blocage
  → remplacements ordonnés
  → frontière d'identifiants
  → fournisseur
```

- **Bloquer ou remplacer le contenu correspondant dans les requêtes inspectées** : Les règles de route s'exécutent avant l'injection de l'authentification du fournisseur. Elles couvrent les corps HTTP décodés pris en charge, les charges utiles Connect JSON non compressées et les messages texte WebSocket. Elles n'inspectent pas les charges utiles gRPC ou Connect Protobuf, les trames Connect compressées, les messages binaires WebSocket, les en-têtes ou les chemins et paramètres d'URL. Une règle ne protège que le contenu avec lequel elle correspond effectivement sur un chemin pris en charge.
- **Adapter délibérément le contenu des requêtes** : Une route peut également réécrire une expression dans une invite ou un champ de modèle lorsque son corps décodé présente une structure clairement identifiable. Il s'agit des mêmes règles de corps que celles utilisées pour les données sensibles.
- **Écarter les identifiants de fournisseur des clients grâce aux routes** : Associez une source d'identifiants à chaque route et remplacez l'authentification uniquement à la frontière de sortie, évitant ainsi la présence de clés d'accès amont dans la configuration des clients.
- **Distribuer les identifiants aux relais appairés avec Vault** : Vault fournit des clés API statiques et gère les cycles d'actualisation OAuth via un RPC mTLS entre Door et Vault, sans relayer le trafic LLM. Pour OAuth, les relais n'empruntent que des jetons d'accès éphémères à la demande, tandis que le matériel d'actualisation ne quitte jamais Vault.
- **Suivre l'utilisation des jetons et les coûts estimés** : gjl enregistre les jetons d'invite, de complétion et de cache rapportés par le fournisseur ainsi que des valorisations de coûts hors ligne en USD dans un registre protégé par le propriétaire. Le suivi de consommation est indépendant de la journalisation du trafic, ne stocke aucun corps d'invite ni secret, et ne nécessite aucun service externe de surveillance.
- **Préserver les corps de réponse du fournisseur** : Le masquage de route ne modifie jamais le corps de la réponse renvoyée au client ; il assainit uniquement une copie d'enregistrement local de taille limitée. Le relais supprime au besoin les en-têtes HTTP hop-by-hop lors du transfert de la réponse.
- **Transmettre les métadonnées d'audit sans les corps de trafic** : Les administrateurs peuvent configurer un collecteur d'audit distant pour rassembler les métadonnées d'événements et de jetons, mais celui-ci ne reçoit que des métadonnées. Les corps des requêtes et des réponses assainies restent strictement confinés au stockage local d'audit protégé par le propriétaire jusqu'à leur suppression explicite.
- **Fonctionner sans dépendance au cloud d'un éditeur** : gjl ne comporte aucun plan de contrôle hébergé, aucun compte de produit, aucune connexion, aucun serveur de licences, aucun enregistrement d'appareil et aucune télémétrie.

## Door, Gate et Vault

Door, Gate et Vault sont des rôles simultanés d'un unique démon (démarré avec `gjl run`), et non des éditions logicielles distinctes.

| Rôle | Mission | Frontière typique |
| --- | --- | --- |
| **Door** | Relais local et standard de commutation de routes | Poste de travail d'un développeur ou serveur local |
| **Gate** | Passerelle TLS partagée, limite de politique d'organisation et point d'injection d'identifiants | Frontière réseau exploitée par un utilisateur ou une organisation |
| **Vault** | Courtier d'identifiants distribuant des clés API et détenant le matériel de rafraîchissement | Frontière dédiée à la gestion des identifiants |

Les architectures de déploiement prises en charge comprennent :

```text
Client LLM --> Door --------------------> Fournisseur
Client LLM --> Door --> Gate -----------> Fournisseur
Client LLM ------------> Gate -----------> Fournisseur
               Door <-> Vault
        RPC d'identifiants uniquement
```

Vault ne reçoit jamais d'invites, de code source, de requêtes ordinaires ni de réponses brutes de fournisseurs.

## Téléchargement de gjl

Téléchargez le package correspondant à votre système d'exploitation et à votre architecture depuis [GitHub Releases](https://github.com/gjl-io/gjl/releases).
Les versions alpha sont marquées comme **Pre-release**. Veuillez lire les notes de version et [vérifier le téléchargement](docs/install.md) avant l'installation. Les bundles pour ordinateur de bureau incluent le binaire `gjl` correspondant.

La version préliminaire initiale ne dispose pas de signature d'éditeur de confiance Windows/macOS ni de notarisation macOS. Le package Windows MSIX n'est donc pas disponible ; macOS peut nécessiter une confirmation manuelle **Ouvrir quand même (Open Anyway)**. Consultez le guide d'installation pour connaître les limites de confiance exactes et les vérifications à effectuer.

| Plateforme | Desktop + `gjl` | `gjl` autonome |
| --- | --- | --- |
| Windows x64 | `gjl-windows-amd64.zip` | `gjl-windows-amd64.exe` |
| Windows Arm64 | — | `gjl-windows-arm64.exe` |
| Linux x64 | `gjl-linux-amd64.deb` ou `gjl-linux-amd64.zip` | `gjl-linux-amd64` |
| Linux Arm64 | `gjl-linux-arm64.deb` ou `gjl-linux-arm64.zip` | `gjl-linux-arm64` |
| macOS Intel | `gjl-darwin-amd64.pkg` ou `gjl-darwin-amd64.zip` | `gjl-darwin-amd64` |
| macOS Apple silicon | `gjl-darwin-arm64.pkg` ou `gjl-darwin-arm64.zip` | `gjl-darwin-arm64` |

### Langues de l'application Desktop

L'application Desktop prend en charge huit langues d'interface. Elle s'adapte aux paramètres régionaux du système et utilise l'anglais par défaut en l'absence de correspondance. Les noms de produits centraux gjl, Door, Gate et Vault restent en anglais dans toutes les langues.

### Gestion des profils en version Alpha

Les versions alpha ne garantissent pas la compatibilité ascendante des fichiers d'état entre différentes versions alpha. Utilisez un nouveau profil lors de l'essai d'une version plus récente. gjl ne supprime ni ne convertit automatiquement un profil antérieur. Exportez ou sauvegardez explicitement les configurations, identifiants, certificats TLS, enregistrements d'appairage, journaux d'audit et données d'utilisation nécessaires avant de changer de profil.

## Prise en main

Les bundles pour ordinateur de bureau incluent la CLI et le démon `gjl`. L'application de bureau gère le démon local via un IPC protégé par le propriétaire. Elle reçoit les identifiants saisis et les transmet au démon ; ce dernier gère le stockage persistant et applique les politiques.

Le routage du trafic LLM à travers gjl nécessite trois éléments :

1. **Une Route** : Définit la cible du fournisseur amont, les règles de masquage et la politique d'authentification pour Door ou Gate. Par défaut, les identifiants clients sont transmis tels quels (passthrough), et l'enregistrement du trafic ainsi que l'audit de masquage sont désactivés.
2. **Un Listener correspondant** : Le point d'entrée du client — soit Door (boucle locale loopback) pour un poste de travail, soit Gate (TLS) pour un accès réseau partagé — lié à cette route. (Les listeners ne peuvent être liés qu'à des routes de même rôle.)
3. **L'URL de base du client LLM** : Pointer votre agent de code, extension d'EDI ou outil de développement vers l'adresse de ce listener.

### Configuration sur Desktop

Dans l'application de bureau, vous pouvez effectuer cette configuration via l'assistant ou manuellement :

- **Configuration rapide (Assistant)** : Cliquez sur **+ (Ajouter)** dans le bandeau supérieur du tableau de bord. Choisir **Utiliser sur cet appareil** regroupe les étapes 1 et 2, créant automatiquement une route Door locale et un listener de boucle locale avec transmission directe des identifiants. Choisir **Partager avec l'équipe** vous guide pour configurer un point de terminaison **Gate** partagé ou un courtier d'identifiants **Vault**.
- **Configuration manuelle** : Ouvrez la vue **Routes** pour créer et inspecter individuellement vos routes et listeners.

> [!TIP]
> **Gestion des identifiants de fournisseur (facultatif) :** Par défaut, gjl relaie les identifiants entrants du client vers le fournisseur sans les stocker. Si vous souhaitez que gjl gère, injecte ou distribue des identifiants au niveau de la frontière, enregistrez d'abord l'identifiant dans le catalogue séparé **Identifiants** avant d'y faire référence dans votre route.

### Gestion sans affichage ou en ligne de commande (CLI)

Dans un environnement sans affichage (headless) ou depuis le terminal, lancez le démon et gérez les entités à l'aide du binaire `gjl` inclus :

```console
$ gjl run
```

Dans un autre terminal :

```console
$ gjl status
$ gjl doctor
$ gjl route --help
$ gjl listener --help
$ gjl --help
```

La CLI et l'application Desktop communiquent via un socket de domaine Unix sous macOS/Linux et un tube nommé (named pipe) sous Windows. Elles n'écrivent jamais directement dans les fichiers de configuration, d'identifiants ou d'audit appartenant au démon.

## Utilisation des règles de remplacement de route

`replace` (remplacement) est une règle s'appliquant au corps de la requête, et non un simple outil de masquage de secrets. Une route ciblée peut remplacer `an apple` par `the green apple` s'il est avéré que cette modification précise améliore une tâche donnée. Elle peut également adapter le modèle demandé par un client de `gpt-5.6-sol` vers `gpt-6-sol` lorsque le fournisseur prend en charge ce modèle plus récent mais que l'outil client ne l'a pas encore intégré. Une réécriture ne permet toutefois pas de rendre disponible un modèle inexistant, ni de modifier un nom de modèle présent uniquement dans un en-tête ou une URL.

**Définissez le motif à partir du corps décodé réel.** Avant d'activer une règle, assurez-vous que son motif d'expression régulière identifie formellement le texte visé. Un simple nom de modèle ou une expression courante peuvent également figurer dans des invites, du code, des exemples ou d'autres champs. Activez temporairement la journalisation du trafic de la route, inspectez le corps de requête local (`body`) dans l'activité de Desktop ou via `gjl audit query`, `gjl audit bodies` et `gjl audit body-save`, puis concevez le motif selon sa structure réelle. Les valeurs d'en-têtes sont exclues du remplacement de corps. Capturez les flux avant d'activer une réécriture si vous devez consulter le corps initial envoyé par le client : le corps conservé dans l'audit correspond à ce qui a été transmis au fournisseur après remplacement. La journalisation du trafic est désactivée par défaut et conserve les corps localement jusqu'à suppression explicite. Les corps enregistrés dans des fichiers séparés doivent faire l'objet d'une suppression distincte.

Par exemple, un corps de requête WebSocket `response.create` capturé utilisait un format JSON compact sans espaces : `{"type":"response.create","model":"gpt-6-sol",...}` avec le champ de modèle encadré de virgules. Pour un client envoyant ce format avec un modèle plus ancien, la règle de route suivante cible ce champ :

```json
{
  "id": "upgrade-model",
  "mode": "replace",
  "pattern": ",\"model\":\"gpt-5\\.6-sol\",",
  "replacement": ",\"model\":\"gpt-6-sol\","
}
```

Cet exemple dépend d'une disposition précise : il ne correspondra pas à un format JSON indenté ni à un champ `model` placé à un autre endroit. Inspectez le corps de la requête du client et adaptez la règle à sa structure effective. gjl utilise la syntaxe d'expressions régulières Go RE2 et applique les règles de remplacement dans l'ordre de la route après avoir évalué toutes les règles de blocage sur le corps décodé d'origine. Les règles ne réécrivent jamais le corps de réponse renvoyé au client ; elles assainissent uniquement la copie locale d'enregistrement.

Pour les règles visant des données sensibles, il peut être pertinent d'indiquer à l'IA cliente que le contenu sortant est réécrit à la frontière réseau. Décrivez le substitut et le comportement attendu sans divulguer le secret lui-même. Le fournisseur recevant la requête réécrite, une consigne au sein de cette requête ne peut pas lui permettre d'accéder au texte d'origine. Pour une route configurée avec `<GJL_MASKED>`, une consigne d'agent peut être rédigée ainsi :

> gjl replaces matching sensitive text with `<GJL_MASKED>` before the provider receives the request. Keep that placeholder intact; do not try to reconstruct its original value.

Vérifiez une requête réelle après avoir modifié une règle, puis désactivez la journalisation temporaire du trafic et supprimez explicitement les événements d'audit inutiles.

Consultez la [compétence de remplacement de route](skills/route-replacements/SKILL.md) pour découvrir le flux de travail permettant de concevoir des règles à partir de la structure observée des requêtes.

## Modèle de sécurité

- Les routes appartiennent strictement soit à Door, soit à Gate. Un listener Door se lie uniquement à des routes Door, et un listener Gate à des routes Gate ; une même route ne peut pas être partagée entre plusieurs rôles.
- Les règles de masquage appartiennent à une route. Chaque règle de blocage examine la requête décodée d'origine avant tout remplacement ; les remplacements s'exécutent ensuite dans l'ordre de la liste.
- L'authentification auprès du fournisseur est gérée indépendamment du masquage de corps et dépend du protocole du fournisseur, non du nom de l'agent de code.
- Les requêtes et identifiants ne transitent jamais par des infrastructures gérées par les créateurs de gjl.
- Door est axé sur le local d'abord (Local-first). Pour un accès partagé ou distant, privilégiez Gate avec les contrôles TLS et CIDR. N'exposez pas de point de terminaison Door sans un contrôle d'accès strict en périphérie.
- Les corps de trafic stockés localement n'expirent pas automatiquement. La suppression constitue une opération de gestion explicite, filtrée ou confirmée.
- Gate peut enregistrer au mieux des métadonnées de clients observés (Observed Client, telles que l'IP source, le User-Agent restreint, les assertions auxiliaires et les empreintes HMAC d'authentification) dans un stockage local séparé et protégé par le propriétaire. Ces observations ne constituent pas des identités humaines vérifiées, et la suppression des événements d'audit n'efface pas ce stockage distinct.
- Un récepteur d'audit distant configuré par l'administrateur peut recevoir des métadonnées (telles que les identifiants d'acteurs ou de clients observés et la consommation de jetons), mais jamais de corps de trafic ni de signaux d'observation bruts. Traitez ces métadonnées comme potentiellement confidentielles lors de la configuration de leur rétention et de leur accès distant.
- Les vérifications de mise à jour ont une valeur purement consultative. Un démon de distribution consulte uniquement les étiquettes publiques de ce dépôt GitHub ; il ne télécharge ni n'installe jamais de mise à jour automatiquement.

Consultez [Accès distant via Gate](docs/remote-exposure.md) avant d'exposer un listener à l'extérieur de son hôte.

## Pourquoi le code source reste privé

Nous estimons que l'IA a grandement facilité la reproduction d'un relais basique, réduisant ainsi l'intérêt de rendre publique son implémentation intégrale. gjl traitant du trafic LLM hautement confidentiel et des identifiants sensibles, nous considérons que publier l'intégralité du code source aiderait d'éventuels attaquants à identifier des failles. C'est pourquoi nous maintenons le code source du produit privé dans le cadre de notre stratégie de sécurité.

Vous pouvez auditer les connexions établies par vos processus gjl à l'aide de notre outil open source en Python [Observateur de connexions](docs/connection-observer.md). Il identifie et étiquette les cibles amont des routes, les flux Gate/Vault, les serveurs OAuth connus ainsi que GitHub ; toute destination non reconnue est classée `UNKNOWN` pour votre examen. Il n'émet aucun jugement subjectif de conformité et ne lit ni les corps de requêtes ni les identifiants.

Après avoir lancé gjl, exécutez la commande suivante à la racine du dépôt :

```sh
python -m pip install -r tools/requirements.txt
python tools/observe_connections.py --duration 600
```

## Contenu du dépôt

Ce dépôt constitue le canal officiel de distribution publique de gjl. Il réunit :

- Les téléchargements officiels des versions et les étiquettes de versions canoniques ;
- La documentation publique d'exploitation et de sécurité ;
- Un [observateur de connexions local](docs/connection-observer.md) optionnel permettant d'identifier les flux réseau visibles ;
- Des compétences d'agent (Agent Skills) facilitant la configuration sécurisée des cas d'usage pris en charge ;
- [`llms.txt`](llms.txt), un guide de tâches pour l'IA couvrant la CLI, Desktop et la documentation du produit.

Les compétences d'agent actuelles couvrent :

- [`skills/gjl-operations`](skills/gjl-operations/SKILL.md) — vérifie la CLI installée et guide l'utilisation des vues Desktop et de l'administration locale.
- [`skills/route-replacements`](skills/route-replacements/SKILL.md) — guide la création de règles de blocage et de remplacement des corps à partir de la structure observée des requêtes (textes sensibles, expressions d'invites, champs de modèles).
- [`skills/remote-exposure`](skills/remote-exposure/SKILL.md) — guide l'appairage mTLS entre Door et Gate et contrôle les limites d'accès distant.

## Rapports de vulnérabilités et licences

Signalez toute vulnérabilité de sécurité de manière confidentielle via le [formulaire de signalement de vulnérabilités de GitHub](https://github.com/gjl-io/gjl/security/advisories/new).
Pour les anomalies non liées à la sécurité, utilisez [GitHub Issues](https://github.com/gjl-io/gjl/issues/new). Ne communiquez aucun secret ni trafic privé dans un ticket public. Consultez [SECURITY.md](SECURITY.md).

Les conditions de licence du dépôt et la licence binaire du produit sont unifiées dans [LICENSE.md](LICENSE.md). Les scripts d'installation publics, les outils Python et les compétences pour agents sont publiés sous [licence MIT](LICENSE-MIT). Les binaires officiels du produit demeurent la propriété exclusive de l'éditeur sous la [licence binaire du produit](PRODUCT-LICENSE.md). Les détails du périmètre sont décrits dans [NOTICE.md](NOTICE.md) et [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Engagements du projet

gjl est conçu selon les principes d'autonomie locale et de pleine maîtrise par l'exploitant :

- Aucun serveur dorsal (backend) ni service hébergé par l'éditeur ;
- Aucun compte produit, aucune connexion obligatoire, aucun verrouillage de fonctionnalités payantes, aucun enregistrement d'appareil ;
- Aucune télémétrie ;
- Aucune transmission de requête, d'identifiant, de configuration ou de donnée d'audit lors des vérifications de version ;
- Aucune installation ou rétrogradation automatique de mise à jour.

Les seules interactions réseau côté éditeur consistent en une consultation non authentifiée des étiquettes publiques GitHub, au téléchargement des composants officiels de la version lorsque l'utilisateur exécute explicitement `gjl update`, et à l'ouverture de la page publique des versions depuis l'interface graphique Desktop à la demande.
