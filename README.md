# XTF zu IFC Konverter
## Überblick
Der XTF zu IFC Konverter ist ein Python-basiertes Tool, das die Konvertierung von XTF-Dateien in IFC-Dateien ermöglicht. Dieses Tool wird verwendet, um die Interoperabilität zwischen verschiedenen Datenformaten sicherzustellen.
## Funktionen
- XTF zu IFC Konvertierung: Konvertiert XTF-Dateien in IFC-Dateien.
- Konfigurationsdatei-Unterstützung: Konfiguration von Eingabe- und Ausgabepfaden über eine config.txt Datei.
- Protokollierung: Detaillierte Protokollierung zur Überwachung des Konvertierungsprozesses und zur Fehlerbehebung.
- Anpassbare Standardwerte: Definieren und Verwenden von Standardwerten für verschiedene Parameter im Konvertierungsprozess.
## Installation
Repository klonen:
```
git clone https://github.com/vaneeko/ili-ifc.git
cd xtf-zu-ifc-konverter
```
Erforderliche Abhängigkeiten installieren:
```
pip install ifcopenshell
Konfiguration
```
Erstellen einer config.txt Datei im Stammverzeichnis des Projekts mit folgendem Format:
```
xtf_files = C:\pfad\zu\xtf\dateien\
output_folder = C:\pfad\zum\ausgabe\ordner\
```
## Nutzung
Starten des Tools mit Python:
```
python xtf_to_ifc.py
```
Das Tool liest die XTF-Dateien aus dem in config.txt angegebenen Verzeichnis, konvertiert sie in IFC-Dateien und speichert die Ausgaben im angegebenen Ausgabeverzeichnis.

## Protokollierung
Protokolle werden erstellt, um detaillierte Informationen über den Konvertierungsprozess bereitzustellen. Diese Protokolle können verwendet werden, um Probleme zu identifizieren und zu beheben, die während der Konvertierung auftreten können.
