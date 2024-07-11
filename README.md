# XTF zu IFC Konverter
## Überblick
Der XTF zu IFC Konverter ist ein Python-basiertes Tool, das die Konvertierung von XTF-Dateien in IFC-Dateien ermöglicht.
### GUI
<div style="overflow: auto;">
    <img src="img/GUI_XTFtoIFC.png" width=40% style="float: left; margin-right: 10px;">
</div>

<div style="clear: both;"></div>

## Funktionen
- XTF zu IFC Konvertierung: Konvertiert XTF-Dateien in IFC-Dateien.
- Konfigurationsdatei-Unterstützung: Konfiguration von Eingabe- und Ausgabepfaden über eine config.txt Datei.
- Protokollierung: Detaillierte Protokollierung zur Überwachung des Konvertierungsprozesses und zur Fehlerbehebung.
- Anpassbare Standardwerte: Definieren und Verwenden von Standardwerten für verschiedene Parameter im Konvertierungsprozess.
  
![Bild der Konvertierungslogik](img/conv.png)
## Installation
Repository klonen:
```
git clone https://github.com/vaneeko/ili-ifc.git
cd ili-ifc
```
Erforderliche Abhängigkeiten installieren (Flask & ifcopenshell):
```
pip install -r requirements.txt
```
## Nutzung
Starten des Tools mit Python:
```
python app.py
```
Navigieren zu: http://127.0.0.1:5000/

## Protokollierung
Protokolle werden erstellt, um detaillierte Informationen über den Konvertierungsprozess bereitzustellen. Diese Protokolle können verwendet werden, um Probleme zu identifizieren und zu beheben, die während der Konvertierung auftreten können.

# Technischer Beschrieb

## Hauptkomponenten

### 1. `app.py`
**Zuständigkeit:** Haupteinstiegspunkt der Anwendung
- Konfiguriert und startet den Flask-Server
- Definiert die Haupt-Routen (/, /convert, /download)
- Initialisiert Hintergrundprozesse (z.B. Dateiaufräumung)

### 2. `api/endpoints.py`
**Zuständigkeit:** API-Endpunkte
- Definiert die REST-API-Endpunkte für die Konvertierung und den Download

### 3. `models/xtf_model.py`
**Zuständigkeit:** XTF-Datenverarbeitung
- Parst XTF-Dateien
- Extrahiert relevante Daten (Haltungen, Normschächte, etc.)
- Berechnet minimale Koordinaten für die Projektausrichtung

### 4. `models/ifc_model.py`
**Zuständigkeit:** IFC-Datengenerierung
- Erstellt die IFC-Projektstruktur
- Generiert IFC-Entitäten für Haltungen und Normschächte
- Handhabt die Koordinatentransformation

### 5. `utils/common.py`
**Zuständigkeit:** Allgemeine Hilfsfunktionen
- Enthält wiederverwendbare Funktionen für IFC-Erstellung und -Manipulation

### 6. `utils/graphics_ns.py`
**Zuständigkeit:** Spezifische Grafikfunktionen
- Enthält Funktionen zur Erstellung von IFC-Geometrien für Normschächte

### 7. `utils/cleanup.py`
**Zuständigkeit:** Aufräumfunktionen
- Handhabt die Bereinigung temporärer Dateien und Verzeichnisse

### 8. `views/templates/index.html`
**Zuständigkeit:** Benutzeroberfläche
- Definiert das HTML-Template für die Weboberfläche

### 9. `views/static/css/styles[1-5].css`
**Zuständigkeit:** Styling
- Enthält verschiedene CSS-Stile für die Benutzeroberfläche

### 10. `config/default_config.py`
**Zuständigkeit:** Standardkonfiguration
- Definiert Standardwerte für verschiedene Parameter des Tools

### 11. `controllers/conversion_controller.py`
**Zuständigkeit:** Konvertierungslogik
- Steuert den Konvertierungsprozess von XTF zu IFC

## Funktionsweise

1. Der Benutzer lädt XTF-Dateien über die Weboberfläche hoch.
2. Die Dateien werden serverseitig verarbeitet:
   a) XTF-Parsing durch `xtf_model.py`
   b) IFC-Generierung durch `ifc_model.py`
3. Die generierten IFC-Dateien werden zum Download bereitgestellt.