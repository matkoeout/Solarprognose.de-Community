# Solarprognose.de (Community Integration for Home Assistant)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[🇩🇪 Deutsch](#-deutsch) | [🇺🇸 English](#-english)

---

<a name="-deutsch"></a>
## 🇩🇪 Deutsch

### WICHTIGER HINWEIS / HAFTUNGSAUSSCHLUSS
DIESE SOFTWARE WIRD **OHNE JEGLICHE GARANTIE** ZUR VERFÜGUNG GESTELLT. DIE NUTZUNG ERFOLGT **AUSSCHLIESSLICH AUF EIGENE GEFAHR**.
Der Autor übernimmt keinerlei Haftung für finanzielle Verluste, falsche Prognosedaten oder Schäden an Hardware/Software. Die Werte sind nicht für Abrechnungszwecke geeignet.

### Beschreibung
Diese Custom Integration bindet die WebAPI von Solarprognose.de ein. Es handelt sich um eine **nicht-offizielle Community-Integration**.

### Funktionsumfang
- Prognose Heute / Morgen / Resttag
- Leistung aktuelle & nächste Stunde
- API-Status & Abfragezähler

### Installation via HACS (Empfohlen)
1. Öffne **HACS** in Home Assistant.
2. Gehe zu **Integrationen**.
3. Klicke oben rechts auf die drei Punkte und wähle **Benutzerdefinierte Repositories**.
4. Füge die URL hinzu: `https://github.com/matkoeout/solarprognose.de-community`
5. Wähle als Kategorie **Integration**.
6. Suche nach "Solarprognose.de" und installiere sie.
7. Starte Home Assistant neu.

### manuelle Installation
1. Kopiere den Ordner `custom_components/solarprognose.de-community` in den lokalen `config/custom_components/` Ordner.
2. Home Assistant neu starten.

### Konfiguration
1. Gehe zu **Einstellungen** -> **Geräte & Dienste**.
2. Klicke auf **Integration hinzufügen**.
3. Suche nach **Solarprognose.de (Community)**.
4. Gib deinen API-Key oder die API-URL ein.

### Sensoren
* **Energie:** today_total, tomorrow_total, rest_day, forecast, current_hour, next_hour
* **Status:** api_status, api_count, last_update, next_update

### Lizenz
MIT Lizenz.
---

<a name="-english"></a>
## 🇺🇸 English

### IMPORTANT NOTICE / DISCLAIMER
THIS SOFTWARE IS PROVIDED **WITHOUT ANY WARRANTY**. USE AT **YOUR OWN RISK**.
The author assumes no liability for financial losses, incorrect forecast data, or damage to hardware/software. These values are not suitable for billing or legal purposes.

### Description
This custom integration connects the Solarprognose.de WebAPI to Home Assistant. This is an **unofficial community integration** and has no affiliation with the operators of Solarprognose.de.

### Features
- Forecast Today / Tomorrow / Remaining Day
- Power Current & Next Hour
- API Status & Request Counter
- Next update time tracking

### Installation via HACS (Recommended)
1. Open **HACS** in Home Assistant.
2. Go to **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Add the URL: `https://github.com/matkoeout/solarprognose.de-community`
5. Select **Integration** as the category.
6. Search for "Solarprognose.de" and install it.
7. Restart Home Assistant.

### Manual Installation
1. Copy the folder `custom_components/solarprognose.de-community` to your `config/custom_components/` directory.
2. Restart Home Assistant.

### Configuration
1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for **Solarprognose.de (Community)**.
4. Enter your API Key or API URL.

### Sensors
* **Energy:** today_total, tomorrow_total, rest_day, forecast, current_hour, next_hour
* **Status:** api_status, api_count, last_update, next_update

### License
MIT License.