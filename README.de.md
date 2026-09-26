# gjl

**Eine selbst gehostete Richtliniengrenze für LLM-Datenverkehr.**

Überprüfen Sie ausgehende Anfragen, blockieren Sie sensible Inhalte oder schreiben Sie dekodierte Anfrage-Bodys mithilfe geordneter Regex-Regeln um, und behalten Sie die vollständige Kontrolle über Provider-Anmeldedaten an einer von Ihnen betriebenen Grenze.

[English](README.md) · [한국어](README.ko.md) · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md)

[Website](https://gjl.io/) · [Releases](https://github.com/gjl-io/gjl/releases) ·
[Installation und Verifizierung](docs/install.md) · [Sicherheitsberichte](SECURITY.md) ·
[Remote-Zugriff](docs/remote-exposure.md) ·
[Verbindungsbeobachter](docs/connection-observer.md) ·
[Lizenzen](LICENSE.md)

## Schnelle Installation & Erste Schritte

Installieren Sie gjl mit einem einzigen Befehl. Das Installationsprogramm erkennt automatisch Ihr Betriebssystem, die CPU-Architektur und die Display-Umgebung, konfiguriert Ihren `PATH` und richtet die passenden Komponenten ein.

### Windows (PowerShell)

```powershell
irm https://gjl.io/install.ps1 | iex
```

*Oder über `curl.exe`:*
```powershell
curl.exe -fsSL https://gjl.io/install.ps1 | powershell -Command -
```

### macOS & Linux (curl)

```bash
curl -fsSL https://gjl.io/install.sh | sh
```

### Nur-CLI-Installation (ohne Desktop-GUI)

Wenn Sie auf einem System mit grafischer Benutzeroberfläche ausschließlich die eigenständige `gjl`-CLI installieren möchten:

* **Windows:**
  ```powershell
  $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
  # oder: & ([scriptblock]::Create((irm https://gjl.io/install.ps1))) -CliOnly
  ```
* **macOS & Linux:**
  ```bash
  curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
  # oder: curl -fsSL https://gjl.io/install.sh | GJL_CLI_ONLY=1 sh
  ```

> [!TIP]
> **Headless- & Server-Umgebungen**: Auf Systemen ohne Display-Server (wie Linux-Servern, Headless-SSH-Sitzungen oder Windows Server Core) überspringt das Installationsprogramm automatisch den Download von Flutter Desktop und installiert nur die eigenständige `gjl`-CLI.

### Ausführung

Direkt nach der Installation in Ihrem aktuellen Terminal:

- **Desktop-GUI:**
  ```bash
  gjl gui
  ```
- **Terminal / Headless:**
  ```bash
  gjl run
  ```

### gjl aktualisieren

Halten Sie Ihre Installation mit `gjl update` auf dem neuesten Stand:

```bash
gjl update             # Aktualisiert alle lokal installierten Komponenten (CLI und/oder Desktop)
gjl update --cli-only  # Aktualisiert nur die gjl-CLI
gjl update --gui-only  # Aktualisiert nur die Desktop-GUI
gjl update --dry-run   # Prüft auf Updates, ohne sie herunterzuladen
```

Informationen zum manuellen Download von Binärdateien und zur Prüfsummenverifizierung finden Sie unter [gjl installieren und überprüfen](docs/install.md).

## Für wen gjl gedacht ist

- **Sicherheitsbewusste Personen und Teams**, die vertrauliche Inhalte blockieren oder maskieren möchten, bevor sie einen Provider erreichen, Provider-Anmeldedaten an einer selbst kontrollierten Grenze halten und optional LLM-Anfragen sowie bereinigte Antwortkopien in lokalen Protokollen erfassen wollen.
- **Benutzer, die bessere LLM-Ergebnisse anstreben**, und Routenregeln nutzen, um Prompt-Formulierungen anzupassen oder innerhalb überprüfbarer Anfragen auf neuere, vom Provider unterstützte Modelle umzuleiten.
- **Organisationen mit mehreren Konten bei einem LLM-Provider**, die für jede Anmeldeinformation eine separate Route wünschen und explizit steuern wollen, welches Konto ein Client verwendet. gjl führt kein automatisches Load Balancing oder Failover zwischen Konten durch.
- **Entwickler und Teams mit mehreren Coding-Agenten-Tools**, die den Token-Verbrauch verfolgen, geschätzte Kosten berechnen und Nutzungsmuster über verschiedene Agenten oder Workflows hinweg vergleichen möchten.
- **Teamleiter und Unternehmen**, die den Token-Verbrauch und die geschätzten Kosten pro Mitglied, Client-Identität oder Anmeldedaten über eine gemeinsame Infrastruktur hinweg aggregieren möchten.

## Was gjl leistet

gjl agiert zwischen einem LLM-Client (z. B. einem Coding-Agenten, einer IDE-Erweiterung oder einem Entwickler-Tool) und einem LLM-Provider. Jede Route gehört entweder zu Door oder Gate und besitzt ihr eigenes Provider-Ziel, ihre Anmeldedatenquelle, Inbound-Authentifizierungsrichtlinie und Maskierungsregeln.

Der geschützte Anforderungspfad verläuft wie folgt:

```text
Dekodierter Body
  → Block-Regel-Vorabprüfung
  → Geordnete Ersetzungen
  → Anmeldedatengrenze
  → Provider
```

- **Passende Inhalte in überprüften Anfragen blockieren oder ersetzen**: Routenregeln werden ausgeführt, bevor die Authentifizierung des Providers eingefügt wird. Sie decken unterstützte dekodierte HTTP-Bodys, unkomprimierte Connect-JSON-Nutzdaten und WebSocket-Textnachrichten ab. Sie überprüfen weder gRPC noch Connect-Protobuf-Nutzdaten, komprimierte Connect-Frames, binäre WebSocket-Nachrichten, Header oder URL-Pfade und Abfrageparameter. Eine Regel schützt nur Inhalte, die auf einem unterstützten Pfad tatsächlich übereinstimmen.
- **Anfrageinhalte gezielt anpassen**: Wenn ein dekodierter Body eine verlässliche Struktur aufweist, kann eine Route Prompt-Phrasen umschreiben oder Modellfelder anpassen. Hierbei kommen dieselben Body-Regeln wie beim Schutz sensibler Daten zum Einsatz.
- **Provider-Anmeldedaten durch Routen von Clients fernhalten**: Jede Route wird an eine einzige Anmeldedatenquelle gebunden, und die Authentifizierung wird erst an der Egress-Grenze ausgetauscht, sodass Upstream-Schlüssel niemals in Client-Konfigurationen verbleiben.
- **Anmeldedaten an gepaarte Relays mit Vault vermitteln**: Vault leitet keinen LLM-Datenverkehr weiter, sondern stellt statische API-Schlüssel bereit und verwaltet OAuth-Aktualisierungszyklen über Door-Vault-mTLS-RPC. Bei OAuth leihen sich Relays bei Bedarf lediglich kurzlebige Zugriffstoken, während das Refresh-Material Vault niemals verlässt.
- **Token-Nutzung und geschätzte Kosten erfassen**: gjl erfasst vom Provider gemeldete Prompt-, Completion- und Cache-Tokens zusammen mit Offline-USD-Kostenberechnungen in einem eigentümergeschützten Hauptbuch. Die Nutzungsverfolgung ist unabhängig von der Datenverkehrsprotokollierung, speichert keine Prompt-Inhalte oder Geheimnisse und benötigt keinen externen Überwachungsdienst.
- **Unveränderte Provider-Antworten an den Client**: Das Maskieren von Routen verändert niemals den an den Client übermittelten Antwort-Body; es bereinigt lediglich eine größenbeschränkte lokale Protokollkopie. Das Relay entfernt bei der Weiterleitung erforderliche HTTP-Hop-by-Hop-Header.
- **Audit-Metadaten ohne Datenverkehrsinhalte weiterleiten**: Administratoren können eine Remote-Audit-Senke konfigurieren, um Ereignis- und Token-Metadaten zu erfassen. Diese empfängt jedoch ausschließlich Metadaten. Anfragen und bereinigte Antwort-Bodys verbleiben strikt im eigentümergeschützten lokalen Speicher, bis sie explizit gelöscht werden.
- **Betrieb ohne Vendor-Cloud**: gjl besitzt keine gehostete Steuerungsebene, keine Benutzerkonten, keine Logins, keine Lizenzserver, keine Geräteregistrierung und keine Telemetrie.

## Door, Gate und Vault

Door, Gate und Vault sind gleichzeitige Fähigkeiten eines einzelnen Daemons (gestartet mit `gjl run`), keine separaten Editionen.

| Rolle | Zweck | Typische Grenze |
| --- | --- | --- |
| **Door** | Lokales Relay und Routen-Schaltstelle | Entwickler-Workstation oder lokaler Server |
| **Gate** | Gemeinsames TLS-Gateway, Unternehmensrichtliniengrenze und Anmeldedateninjektionspunkt | Eine vom Benutzer oder der Organisation betriebene Netzwerkgrenze |
| **Vault** | Anmeldedaten-Broker, der API-Schlüssel bereitstellt und Refresh-Material besitzt | Eine dedizierte Grenze für Anmeldedaten |

Zu den unterstützten Bereitstellungspfaden gehören:

```text
LLM-Client --> Door --------------------> Provider
LLM-Client --> Door --> Gate -----------> Provider
LLM-Client ------------> Gate -----------> Provider
               Door <-> Vault
            nur Anmeldedaten-RPC
```

Vault empfängt niemals Prompts, Quellcode, reguläre Anfragen oder unverarbeitete Antworten.

## gjl herunterladen

Laden Sie das entsprechende Paket für Ihr Betriebssystem und Ihre Architektur von den [GitHub Releases](https://github.com/gjl-io/gjl/releases) herunter.
Alpha-Versionen sind als **Pre-release** gekennzeichnet. Lesen Sie die Versionshinweise und [überprüfen Sie den Download](docs/install.md) vor der Installation. Desktop-Bundles enthalten die passende `gjl`-Binärdatei.

Der anfänglichen Vorabversion fehlen plattformzertifizierte Entwicklersignaturen für Windows/macOS sowie die macOS-Notarisierung. Windows MSIX ist daher nicht verfügbar; macOS erfordert möglicherweise die Auswahl von **Dennoch öffnen (Open Anyway)**. Beachten Sie die Installationsanleitung für genaue Prüfschritte.

| Plattform | Desktop + `gjl` | Eigenständiges `gjl` |
| --- | --- | --- |
| Windows x64 | `gjl-windows-amd64.zip` | `gjl-windows-amd64.exe` |
| Windows Arm64 | — | `gjl-windows-arm64.exe` |
| Linux x64 | `gjl-linux-amd64.deb` oder `gjl-linux-amd64.zip` | `gjl-linux-amd64` |
| Linux Arm64 | `gjl-linux-arm64.deb` oder `gjl-linux-arm64.zip` | `gjl-linux-arm64` |
| macOS Intel | `gjl-darwin-amd64.pkg` oder `gjl-darwin-amd64.zip` | `gjl-darwin-amd64` |
| macOS Apple silicon | `gjl-darwin-arm64.pkg` oder `gjl-darwin-arm64.zip` | `gjl-darwin-arm64` |

### Desktop-Sprachen

Die Desktop-App unterstützt acht Benutzeroberflächensprachen. Sie folgt dem Systemgebietsschema und greift auf Englisch zurück, wenn keine passende Sprache gefunden wird. Die Kernproduktnamen gjl, Door, Gate und Vault bleiben in allen Sprachen auf Englisch.

### Hinweise zu Alpha-Profilen

Alpha-Versionen garantieren keine Abwärtskompatibilität der Statusdateien mit späteren Alphas. Verwenden Sie ein neues Profil, wenn Sie eine neuere Alpha testen. gjl löscht oder konvertiert ältere Profile nicht automatisch. Exportieren oder sichern Sie Konfigurationen, Anmeldedaten, TLS-Zertifikate, Pairing-Datensätze, Audit- und Nutzungsdaten explizit, bevor Sie Profile wechseln.

## Erste Schritte

Desktop-Pakete enthalten die `gjl`-CLI und den Daemon. Die Desktop-App verwaltet den lokalen Daemon über eigentümergeschützte IPC. Sie nimmt eingegebene Anmeldedaten entgegen und übergibt sie dem Daemon; der Daemon verwaltet die persistente Speicherung und setzt Richtlinien durch.

Das Routing von LLM-Datenverkehr über gjl erfordert im Wesentlichen drei Elemente:

1. **Eine Route**: Definiert das Upstream-Ziel, Maskierungsregeln und die Authentifizierungsrichtlinie für Door oder Gate. Standardmäßig werden Client-Anmeldedaten unverändert durchgereicht (passthrough), und Protokollierungen sind deaktiviert.
2. **Ein passender Listener**: Der Client-Einstiegspunkt – entweder Door (lokales Loopback) für eine Workstation oder Gate (TLS) für den Netzwerkzugriff –, der an diese Route gebunden ist. (Listener binden nur an Routen derselben Rolle.)
3. **Die Base-URL des LLM-Clients**: Konfigurieren Sie Ihren Coding-Agenten, Ihre IDE-Erweiterung oder Ihr Entwicklertool so, dass sie auf die Adresse dieses Listeners verweisen.

### Desktop-Einrichtung

In der Desktop-App können Sie die Konfiguration über den Einrichtungsassistenten oder manuell vornehmen:

- **Schnelleinrichtung (Assistent)**: Klicken Sie im oberen Dashboard-HUD auf **+ (Hinzufügen)**. Die Auswahl von **Auf diesem Gerät verwenden** bündelt Schritt 1 und 2 und erstellt automatisch eine lokale Door-Route und einen Loopback-Listener mit Anmeldedaten-Passthrough. **Mit Team teilen** führt Sie durch die Konfiguration eines gemeinsamen **Gate**-Endpunkts oder eines **Vault**-Brokers.
- **Manuelle Einrichtung**: Öffnen Sie die Ansicht **Routen**, um Routen und Listener individuell zu erstellen und zu überprüfen.

> [!TIP]
> **Verwaltung von Provider-Anmeldedaten (optional):** Standardmäßig leitet gjl eingehende Client-Anmeldedaten an den Provider weiter, ohne sie zu speichern. Wenn Sie möchten, dass gjl Anmeldedaten an der Grenze verwaltet, injiziert oder vermittelt, registrieren Sie die Anmeldedaten zuerst im separaten Katalog **Anmeldedaten**, bevor Sie in einer Route darauf verweisen.

### Headless- oder CLI-Verwaltung

In einer Headless-Umgebung oder über die Befehlszeile starten Sie den Daemon und verwalten Instanzen über die integrierte `gjl`-Binärdatei:

```console
$ gjl run
```

In einem anderen Terminal:

```console
$ gjl status
$ gjl doctor
$ gjl route --help
$ gjl listener --help
$ gjl --help
```

CLI und Desktop kommunizieren unter macOS/Linux über Unix-Domain-Sockets und unter Windows über Named Pipes. Sie greifen niemals direkt auf daemon-eigene Konfigurationen, Anmeldedaten oder Audit-Speicher zu.

## Routen-Ersetzungsregeln verwenden

`replace` (Ersetzen) ist eine Request-Body-Regel, nicht nur ein Maskierer für Geheimnisse. Eine eng gefasste Route kann beispielsweise `an apple` durch `the green apple` ersetzen, wenn sich gezeigt hat, dass genau diese Änderung ein Arbeitsergebnis verbessert. Ebenso kann das angeforderte Modell von `gpt-5.6-sol` auf `gpt-6-sol` aktualisiert werden, wenn der Provider das neuere Modell unterstützt, das Client-Tool jedoch noch nicht aktualisiert wurde. Eine Ersetzung kann jedoch kein nicht vorhandenes Modell verfügbar machen oder Modellnamen ändern, die ausschließlich im Header oder der URL übertragen werden.

**Wählen Sie das Muster anhand des tatsächlich dekodierten Bodys.** Prüfen Sie vor der Aktivierung einer Regel, ob das Regex-Muster den beabsichtigten Text eindeutig identifiziert. Ein bloßer Modellname oder alltägliche Begriffe können auch in Prompts, Code oder Beispielen vorkommen. Aktivieren Sie vorübergehend das Traffic-Protokoll der Route, analysieren Sie die lokale Anfrage (`body`) im Desktop-Aktivitätsfeed oder über `gjl audit query`, `gjl audit bodies` und `gjl audit body-save`, und erstellen Sie auf dieser Basis das Muster. Header-Werte fallen nicht unter die Body-Ersetzung. Führen Sie die Erfassung vor der Aktivierung durch, wenn Sie den ursprünglichen Body des Clients sehen müssen: Das Audit-Protokoll zeichnet den Body auf, wie er nach der Ersetzung an den Provider gesendet wurde. Das Traffic-Protokoll ist standardmäßig deaktiviert und speichert Bodys lokal bis zur expliziten Löschung. In separate Dateien exportierte Bodys müssen separat gelöscht werden.

Beispielsweise verwendete ein erfasster WebSocket-`response.create`-Anfrage-Body kompaktes JSON ohne Leerzeichen: `{"type":"response.create","model":"gpt-6-sol",...}` mit durch Kommas umschlossenem Modellfeld. Für einen Client, der dasselbe Format mit dem älteren Modell sendet, lautet die passende Regel:

```json
{
  "id": "upgrade-model",
  "mode": "replace",
  "pattern": ",\"model\":\"gpt-5\\.6-sol\",",
  "replacement": ",\"model\":\"gpt-6-sol\","
}
```

Dieses Beispiel ist formatspezifisch: Es greift nicht bei formatiertem (pretty-printed) JSON oder wenn sich das Feld an anderer Stelle befindet. Überprüfen Sie den Body Ihres Clients und passen Sie die Regel an. gjl verwendet die Go-RE2-Regex-Syntax und wendet Ersetzungsregeln in Routen-Reihenfolge an, nachdem alle Block-Regeln gegen den ursprünglichen dekodierten Body geprüft wurden. Regeln verändern niemals die an den Client zurückgesendete Antwort; sie bereinigen lediglich die lokale Protokollkopie.

Bei Maskierungsregeln für vertrauliche Texte kann es hilfreich sein, der clientseitigen KI mitzuteilen, dass ausgehende Inhalte an der Netzwerkgrenze ersetzt werden. Beschreiben Sie den Platzhalter und das erwartete Verhalten, ohne das Geheimnis selbst zu nennen. Da der Provider die ersetzte Anfrage empfängt, kann eine Anweisung innerhalb dieser Anfrage den Originaltext nicht rekonstruieren. Für eine Route mit `<GJL_MASKED>` könnte ein Agenten-Hinweis wie folgt lauten:

> gjl replaces matching sensitive text with `<GJL_MASKED>` before the provider receives the request. Keep that placeholder intact; do not try to reconstruct its original value.

Überprüfen Sie tatsächliche Anfragen nach dem Anpassen einer Regel, deaktivieren Sie die temporäre Protokollierung und löschen Sie nicht mehr benötigte Audit-Ereignisse explizit.

Einen strukturierten Arbeitsablauf zur Ausarbeitung von Regeln finden Sie im [Route Replacement Skill](skills/route-replacements/SKILL.md).

## Sicherheitsmodell

- Routen gehören strikt entweder zu Door oder zu Gate. Ein Door-Listener bindet nur an Door-Routen, während ein Gate-Listener nur an Gate-Routen bindet; eine Route kann nicht über Rollen hinweg geteilt werden.
- Maskierungsregeln gehören zu einer Route. Jede Blockierungsregel prüft die ursprüngliche dekodierte Anfrage, bevor Ersetzungen stattfinden; Ersetzungen laufen anschließend in Listenreihenfolge ab.
- Die Provider-Authentifizierung erfolgt unabhängig von der Maskierung und richtet sich nach dem Protokollmechanismus des Providers, nicht nach dem Namen eines Coding-Agenten.
- Anfragen und Anmeldedaten gelangen niemals über Infrastrukturen der gjl-Entwickler.
- Door arbeitet lokal priorisiert (Local-first). Verwenden Sie für Fernzugriff oder gemeinsame Nutzung Gate mit TLS- und CIDR-Kontrollen. Veröffentlichen Sie niemals einen Door-Endpunkt ohne strikte Zugriffskontrollen.
- Lokale Datenverkehrs-Bodys verfallen nicht automatisch. Die Löschung ist ein expliziter, gefilterter oder bestätigungspflichtiger Vorgang.
- Gate kann Metadaten beobachteter Clients (Observed Client, z. B. Quell-IP, User-Agent, Hilfsansprüche, HMAC-Authentifizierungs-Fingerabdrücke) nach bestem Bemühen in einem separaten lokalen Speicher erfassen. Diese stellen keine verifizierten menschlichen Identitäten dar; das Löschen von Audit-Ereignissen löscht diesen Speicher nicht.
- Eine vom Operator konfigurierte Remote-Audit-Senke kann Metadaten (wie Token-Nutzung und Client-Identifikatoren) empfangen, jedoch niemals Datenverkehrs-Bodys oder rohe Beobachtungssignale. Behandeln Sie diese Metadaten bei der Aufbewahrungskonfiguration als potenziell sensibel.
- Update-Prüfungen sind rein informativ (advisory). Ein Release-Daemon liest ausschließlich öffentliche Tags aus diesem GitHub-Repository; er lädt niemals Updates automatisch herunter oder installiert diese.

Lesen Sie [Remote-Zugriff über Gate](docs/remote-exposure.md), bevor Sie einen Listener außerhalb seines Hosts erreichbar machen.

## Warum der Quellcode privat bleibt

Wir sind der Ansicht, dass KI die Neuerstellung grundlegender Relays erleichtert hat, wodurch der Nutzen einer Veröffentlichung des Codes gesunken ist. Da gjl hochsensiblen LLM-Datenverkehr und Anmeldedaten verarbeitet, würde eine vollständige Offenlegung des Quellcodes es Angreifern erleichtern, Schwachstellen aufzuspüren. Die Beibehaltung des Quellcodes als proprietäre Software ist daher Teil unseres Sicherheitskonzepts.

Sie können mit unserem quelloffenen Python-[Verbindungsbeobachter](docs/connection-observer.md) genau prüfen, wohin Ihre laufenden gjl-Prozesse Verbindungen aufbauen. Er kennzeichnet sichtbare Routen-Upstreams, Gate/Vault-Verbindungen, bekannte OAuth-Server und GitHub; unidentifizierte Ziele werden als `UNKNOWN` ausgewiesen. Das Tool trifft keine Sicherheitsurteile und liest weder Anfragedaten noch Zugangsdaten.

Starten Sie gjl und führen Sie im Repository-Stammverzeichnis Folgendes aus:

```sh
python -m pip install -r tools/requirements.txt
python tools/observe_connections.py --duration 600
```

## Repository-Inhalt

Dieses Repository ist die öffentliche Vertriebsplattform für gjl. Es enthält:

- Offizielle Release-Downloads und standardisierte Versions-Tags;
- Öffentliche Betriebs- und Sicherheitsdokumentationen;
- Einen optionalen lokalen [Verbindungsbeobachter](docs/connection-observer.md);
- Agent Skills zur sicheren Konfiguration unterstützter Arbeitsabläufe;
- [`llms.txt`](llms.txt), einen KI-Aufgabenleitfaden für CLI, Desktop und Produktdokumentation.

Aktuelle Agent Skills umfassen:

- [`skills/gjl-operations`](skills/gjl-operations/SKILL.md) — Prüft die installierte CLI und führt durch Desktop-Ansichten und lokale Verwaltung.
- [`skills/route-replacements`](skills/route-replacements/SKILL.md) — Entwickelt Blockier- und Ersetzungsregeln für Bodies anhand beobachteter Anforderungsstrukturen (inklusive sensibler Texte, Prompt-Phrasen und Modellfelder).
- [`skills/remote-exposure`](skills/remote-exposure/SKILL.md) — Leitet das Door-Gate-mTLS-Pairing an und überprüft Sicherheitsgrenzen für den Remote-Zugriff.

## Fehlerberichte und Lizenzierung

Melden Sie Sicherheitslücken vertraulich über das [GitHub-Formular für Sicherheitsberichte](https://github.com/gjl-io/gjl/security/advisories/new).
Verwenden Sie [GitHub Issues](https://github.com/gjl-io/gjl/issues/new) für allgemeine Fehler. Fügen Sie öffentlichen Issues niemals Geheimnisse oder privaten Datenverkehr bei. Siehe [SECURITY.md](SECURITY.md).

Die Lizenzbedingungen des Repositorys und die Produkt-Binärlizenz sind in [LICENSE.md](LICENSE.md) zusammengefasst. Die öffentlichen Installationsskripte, Python-Tools und Agent Skills stehen unter der [MIT-Lizenz](LICENSE-MIT). Offizielle Produkt-Binärdateien verbleiben proprietär unter der [Produkt-Binärlizenz](PRODUCT-LICENSE.md). Der genaue Geltungsbereich ist in [NOTICE.md](NOTICE.md) und [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) beschrieben.

## Projektgarantien

gjl basiert auf dem Prinzip lokaler und betreibergeführter Autorität:

- Kein vom Anbieter betriebenes Backend oder Cloud-Dienst;
- Kein Produktkonto, kein Login, keine Sperre für kostenpflichtige Funktionen und keine Geräteregistrierung;
- Keine Telemetrie;
- Keine Provider-Anfragen, Anmeldedaten, Konfigurationen oder Audit-Daten bei Update-Prüfungen;
- Keine automatische Installation oder Rollback von Updates.

Die einzigen netzwerkseitigen Anbieterinteraktionen bestehen im unauthentifizierten Auslesen öffentlicher GitHub-Tags, dem Herunterladen offizieller Release-Assets bei expliziter Ausführung von `gjl update` durch den Benutzer und dem Öffnen der öffentlichen Release-Seite über die Desktop-GUI auf Anforderung.
