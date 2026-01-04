# Solarprognose.de (Community Integration für Home Assistant)

## WICHTIGER HINWEIS / HAFTUNGSAUSSCHLUSS

DIESE SOFTWARE WIRD **OHNE JEGLICHE GARANTIE** ZUR VERFÜGUNG GESTELLT.

DIE NUTZUNG ERFOLGT **AUSSCHLIESSLICH AUF EIGENE GEFAHR**.

DER AUTOR ÜBERNIMMT **KEINERLEI HAFTUNG** FÜR:
- FALSCHE, UNVOLLSTÄNDIGE ODER VERALTETE PROGNOSEDATEN
- FINANZIELLE VERLUSTE, ENTGANGENE ERTRÄGE ODER FEHLENTSCHEIDUNGEN
- FEHLFUNKTIONEN, AUSFÄLLE ODER DATENVERLUSTE
- SCHÄDEN AN HARDWARE, SOFTWARE ODER PV-ANLAGEN
- FOLGESCHÄDEN JEGLICHER ART

INSBESONDERE SIND DIE BERECHNETEN PROGNOSEWERTE **NICHT** FÜR:
- ABRECHNUNGEN
- GARANTIE- ODER GEWÄHRLEISTUNGSZWECKE
- VERTRAGLICHE ODER RECHTLICHE ENTSCHEIDUNGEN
- KRITISCHE STEUERUNGEN

GEEIGNET.

MIT DER INSTALLATION UND NUTZUNG DIESER INTEGRATION ERKLÄRST DU DICH AUSDRÜCKLICH DAMIT EINVERSTANDEN.

---

## Beschreibung

Diese Custom Integration für Home Assistant bindet die WebAPI von Solarprognose.de ein und stellt PV-Ertragsprognosen als Sensoren zur Verfügung.

Es handelt sich um eine **nicht-offizielle Community-Integration**. Es besteht **keine Verbindung** zum Betreiber von Solarprognose.de.

---

## Funktionsumfang

- Prognose des heutigen Gesamtertrags
- Prognose des morgigen Gesamtertrags
- Prognose des verbleibenden Tagesertrags
- Leistung aktuelle Stunde
- Leistung nächste Stunde
- Aggregierte Tagesprognose (nicht für das Energy Dashboard geeignet)
- Anzeige der nächsten erlaubten API-Abfragezeit
- Zähler für tägliche API-Aufrufe
- API-Status- und Fehlermeldungssensor

---

## Installation

### Installation über HACS (empfohlen)

1. HACS öffnen
2. Integrationen → Benutzerdefinierte Repositories
3. Repository hinzufügen:
   https://github.com/matkoeout/link_solarprognose_de
4. Kategorie: Integration
5. Integration installieren
6. Home Assistant neu starten

---

### Manuelle Installation

1. Ordner
   custom_components/link_solarprognose_de
   nach
   config/custom_components/
   kopieren
2. Home Assistant neu starten

---

## Konfiguration

Die Konfiguration erfolgt vollständig über die Benutzeroberfläche von Home Assistant.

### Integration hinzufügen

Einstellungen → Geräte & Dienste → Integration hinzufügen → Solarprognose.de (Community)

### Zugangsdaten

Erforderlich ist mindestens eine der folgenden Angaben:

- API-Key von Solarprognose.de
- Vollständige API-URL

Ohne gültige Zugangsdaten ist kein Betrieb möglich.

---

## Optionen

API-Key oder API-URL können jederzeit unter den Integrationsoptionen geändert werden. Die Integration wird danach automatisch neu geladen.

---

## Sensoren

### Energie

- Heute Gesamt (kWh)
- Morgen Gesamt (kWh)
- Resttag (kWh)
- Prognose (kWh)

---

### Leistung

- Aktuelle Stunde (W)
- Nächste Stunde (W)

---

### Status

- API Status
- API Abfragen heute
- Letzte erfolgreiche Abfrage
- Nächste erlaubte Abfragezeit

---

## Update-Intervall

Standardmäßig erfolgt eine Aktualisierung alle 150 Minuten unter Berücksichtigung der von der API vorgegebenen Abfragezeit.

---

## Kompatibilität

- Home Assistant Version 2023.6 oder neuer
- Config Flow Unterstützung
- HACS-kompatibel

---

## Lizenz

MIT License.

---

## Schlussbestimmung

DER AUTOR KANN DIE FUNKTION DER SOFTWARE JEDERZEIT ÄNDERN ODER EINSTELLEN.
ES BESTEHT KEIN ANSPRUCH AUF SUPPORT, WARTUNG ODER WEITERENTWICKLUNG.

