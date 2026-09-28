# Home Assistant Zeitmanager

Lokaler Zeitmanager für Home Assistant mit eigener Dashboard-Karte.

Der Zeitmanager schaltet Geräte nach **Uhrzeit**, **Sonnenaufgang**, **Sonnenuntergang** oder über einen **Countdown-Timer**. Mehrere Zeitpläne pro Gerät und unterschiedliche Wochentage werden unterstützt.

## Unterstützte Geräte

- Switch
- Light
- Climate
- Cover / Rollläden
- Fan

Bei Climate-Geräten können HVAC-Modus und Solltemperatur festgelegt werden. Bei Cover-Geräten können getrennte Positionen für EIN/Öffnen und AUS/Schließen eingestellt werden.

## Funktionen

- beliebig viele Geräte
- mehrere Zeitpläne pro Gerät
- feste Uhrzeiten
- Sonnenaufgang und Sonnenuntergang
- positiver oder negativer Minuten-Offset
- Wochentage frei auswählbar
- Zeiträume über Mitternacht
- Countdown-Timer mit Schnellwahl 30 / 60 / 120 Minuten
- individuelle Timerdauer
- automatisches Ausschalten nach Timerende
- Climate-Modus und Solltemperatur
- Rollladenpositionen 0–100 %
- komplette Zeitsteuerung ein-/ausschaltbar
- einzelne Geräte aktivier-/deaktivierbar
- Anzeige von Status und nächster Aktion
- Deutsch und Englisch
- Steuerung läuft im Backend weiter, auch wenn kein Dashboard geöffnet ist
- lokale Speicherung in Home Assistant
- HACS-kompatibel

## Installation über HACS

1. HACS öffnen.
2. **Integrationen** auswählen.
3. Menü oben rechts → **Benutzerdefinierte Repositories**.
4. Dieses Repository eintragen: `https://github.com/Roy-82/ha-time-manager`
5. Kategorie **Integration** auswählen.
6. **Zeitmanager** installieren.
7. Home Assistant neu starten.
8. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Zeitmanager**.

## Dashboard-Karte

Unter **Einstellungen → Dashboards → Ressourcen** einmalig hinzufügen:

- URL: `/time_manager/time-manager-card.js?v=0.1.0`
- Typ: **JavaScript-Modul**

Danach eine manuelle Karte anlegen:

```yaml
type: custom:time-manager-card
entity: sensor.zeitmanager
title: Zeitmanager
```

Falls Home Assistant dem Sensor einen anderen Entity-Namen gibt, den tatsächlichen Sensor verwenden.

## Bedienung

- **+** Gerät hinzufügen
- **−** markiertes Gerät entfernen
- **✎** markiertes Gerät bearbeiten

Im Geräteeditor können beliebig viele Zeitpläne hinzugefügt werden.

### Beispiel Außenbeleuchtung

EIN: Sonnenuntergang −20 Minuten  
AUS: 23:30 Uhr

### Beispiel Rollladen

EIN/Öffnen: 07:00 Uhr → Position 100 %  
AUS/Schließen: Sonnenuntergang +15 Minuten → Position 0 %

### Beispiel Klima

EIN: 16:00 Uhr  
AUS: 22:00 Uhr  
HVAC-Modus: `heat_cool`  
Solltemperatur: 20 °C

## Timer

Direkt in der Geräteliste stehen Schnell-Timer mit 30, 60 und 120 Minuten zur Verfügung. Über **…** kann eine eigene Dauer eingegeben werden.

Der Zeitmanager erzeugt keine Home-Assistant-Automationen. Die Zeitpläne werden von der Integration selbst verwaltet.

Version: **0.1.0**
