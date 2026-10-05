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
- Countdown-Timer mit drei je Gerät frei konfigurierbaren Schnellwahlzeiten (Standard 30 / 60 / 90 Minuten)
- individuelle Timerdauer
- kompakte Geräteübersicht mit Checkbox zum Aktivieren/Deaktivieren der Zeitsteuerung
- Geräteübersicht zeigt nur Name, Entität und nächste Schaltung
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

- URL: `/time_manager/time-manager-card.js?v=0.2.0`
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

## Geräteübersicht

Die Übersicht bleibt bewusst kompakt. Pro Gerät werden nur der gewählte Name, die Entität und die nächste Schaltung angezeigt. Links aktiviert oder deaktiviert eine Checkbox die Zeitsteuerung dieses Geräts. Rechts stehen +, − und ✎ vertikal zentriert neben der Geräteliste.

## Timer

Die Timer-Bedienung befindet sich im Geräteeditor hinter **✎**. Pro Gerät können drei Schnellwahlzeiten frei festgelegt werden; Standard sind 30, 60 und 90 Minuten. Dort lassen sich die Schnell-Timer direkt starten, über **…** eine freie Dauer eingeben und ein laufender Timer abbrechen.

Der Zeitmanager erzeugt keine Home-Assistant-Automationen. Die Zeitpläne werden von der Integration selbst verwaltet.

Version: **0.2.0**
