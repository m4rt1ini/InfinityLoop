# InfinityLoop

InfinityLoop ist eine Python-basierte Desktop-Anwendung zur Generierung von nahtlosen Video-Loops. Die Videoverarbeitung erfolgt über FFmpeg, während FastAPI und PyWebView als Basis für das GUI dienen.

## Kernfunktionen
* **Loop-Modi:**
  * **Hardcut:** Direkte Konkatenation des Eingabevideos über den FFmpeg Concat-Demuxer (Stream-Copy ohne Re-Encoding).
  * **Ping-Pong:** Hängt eine rückwärts abgespielte Kopie des Videostreams an das Original an.
  * **Crossdissolve:** Nutzt den `xfade`-Filter für Video und `acrossfade` für Audio, um die Schnittkanten überzublenden.
* **Audio-Wrapping (Asynchroner Schnitt):** Ermöglicht die Verschiebung der Audiospur relativ zur Videospur, um den Schnittpunkt akustisch zu verbergen.
* **Hardwarebeschleunigung:** Automatische Erkennung und Nutzung verfügbarer Hardware-Encoder:
  * NVENC (`h264_nvenc`, `hevc_nvenc`, `av1_nvenc`) für NVIDIA GPUs.
  * VideoToolbox (`h264_videotoolbox`, `hevc_videotoolbox`, `av1_videotoolbox`) für macOS.
  * Fallbacks auf Software-Encoding (`libx264`, `libx265`, `libsvtav1`).
* **UI & Dateihandling:** Das Frontend wird von FastAPI bereitgestellt und lokal in einem nativen Webview-Fenster (PyWebView) gerendert. Die Dateiauswahl erfolgt über native OS-Dialoge (`tkinter`), um Browser-Upload-Latenzen zu vermeiden.
* **Asynchrone Verarbeitung:** FFmpeg-Prozesse laufen im Hintergrund. Der Renderfortschritt wird über die stdout-Ausgabe von FFmpeg (`-progress`) geparst und über Server-Sent Events (SSE) an das Frontend gestreamt.

## Systemvoraussetzungen
* **Betriebssystem:** Windows, macOS oder Linux.
* **Python:** Installiert und in der System-PATH-Variable hinterlegt.
* **FFmpeg:** Die Binaries `ffmpeg` und `ffprobe` müssen installiert und global über die PATH-Variable aufrufbar sein.

## Installation & Ausführung
1. Repository klonen.
2. Sicherstellen, dass FFmpeg installiert ist.
3. Das Programm über das mitgelieferte Batch-Skript starten:
   ```cmd
   start.bat
   ```
   *Hinweis: Die `start.bat` installiert fehlende Python-Abhängigkeiten (`fastapi`, `uvicorn`, `python-multipart`, `pywebview`) automatisch via pip und führt anschließend `main.py` aus.*

## Architektur
* `backend/main.py`: FastAPI-Webserver, SSE-Endpunkte und PyWebView-Instanz.
* `backend/video_processor.py`: FFmpeg-Wrapper, Berechnung der Video-Dauer und dynamischer Filtergraphen.
* `frontend/`: Statische Assets (HTML, CSS, JS), die direkt vom Backend ausgeliefert werden.
