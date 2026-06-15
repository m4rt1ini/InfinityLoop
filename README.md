# InfinityLoop - Video Generator

Ein extrem schneller, hardwarebeschleunigter Video-Loopgenerator, der speziell für riesige Dateien (bis zu 15 GB+) und flüssige Übergänge entwickelt wurde. Dank nativer Desktop-Integration fühlt sich InfinityLoop wie eine echte App an – keine Browser-Upload-Wartezeiten und kein Konsolen-Chaos.

## ✨ Features
* **Native Desktop App:** Läuft als sauberes, eigenständiges Fenster (ohne Browser-Tabs). Schließt du das Fenster, beendet sich das Programm sauber im Hintergrund.
* **Echtzeit-Ladebalken:** Verfolge den Renderfortschritt auf die Millisekunde genau durch direkte FFmpeg-Stream-Analyse (via Server-Sent Events).
* **Null-Upload-Delay:** Das Eingabevideo wird nicht über den Browser "hochgeladen", sondern direkt über native Dateidialoge referenziert. Die Verarbeitung startet sofort!
* **Drei intelligente Loop-Modi:**
  * **Hardcut**: Aneinanderreihung des Videos ohne Wartezeiten durch FFmpeg Concat-Demuxer.
  * **Ping-Pong**: Vorwärts- und Rückwärts-Wiedergabe.
  * **Crossdissolve**: Harte Schnitte werden durch fließende, einstellbare Bild- und Ton-Überblendungen kaschiert.
* **Audio-Versatz (L-Cut / J-Cut):** Verschiebe die Tonspur asynchron zum Bild ("Audio-Wrapping"), um Loop-Sprünge für das Gehirn komplett unsichtbar zu machen.
* **Cross-Platform Hardwarebeschleunigung:** Erkennt automatisch die beste Grafikkarte:
  * **Windows/Linux**: NVIDIA NVENC (h264_nvenc, hevc_nvenc, av1_nvenc)
  * **Apple Mac**: VideoToolbox (h264_videotoolbox, hevc_videotoolbox, av1_videotoolbox)
  * **Fallback**: CPU-Rendering, falls keine GPU vorhanden ist.
* **Modernste Codecs:** Wähle flexibel zwischen H.264, HEVC (H.265) und Next-Gen AV1.

## 🛠 Voraussetzungen
* **Betriebssystem:** Windows, macOS oder Linux.
* **Python:** Installiert (mit Umgebungsvariable PATH).
* **FFmpeg:** Installiert (mit Umgebungsvariable PATH - das Skript ruft `ffmpeg` und `ffprobe` auf).

## 🚀 Installation & Erster Start
Das Programm installiert bei ersten Start seine Python-Abhängigkeiten (FastAPI, Uvicorn, PyWebView) automatisch.

1. Lade dir FFmpeg herunter und füge es zu deinen Systemvariablen hinzu.
2. Mache einen **Doppelklick auf die Datei `start.bat`**.

Das Programm installiert kurz eventuell fehlende Pakete (`requirements.txt`) und öffnet danach direkt die wunderschöne, fensterbasierte App.

## 🎬 Benutzung
1. Klicke auf **Video wählen** – es öffnet sich sofort der native Windows/Mac Dateidialog.
2. Wähle deinen Loop-Modus (Hardcut, Ping-Pong, Crossfade).
3. Passe bei Bedarf den Audio-Versatz (asynchroner Schnitt) an.
4. Wähle unten das Ziel-Format und den **Speicherort** aus.
5. Klicke auf Generieren und beobachte den Live-Ladebalken! 

## 📁 Projektstruktur
* `/backend`: Beinhaltet den Python-Server (`main.py`), der auch das GUI rendert, und die FFmpeg-Logik (`video_processor.py`).
* `/frontend`: Beinhaltet die grafische Benutzeroberfläche (HTML, CSS, JS).
* `start.bat`: Die komfortable "One-Click"-Startdatei für Anwender.
