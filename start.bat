@echo off
echo Starte InfinityLoop Generator...

:: Wechsle ins Backend-Verzeichnis
cd backend

:: Stelle sicher, dass alle Pakete installiert sind (inkl. pywebview)
python -m pip install -r requirements.txt -q

:: Starte die App. Das oeffnet das Fenster und blockiert die Konsole bis es geschlossen wird.
python main.py

echo.
echo Programm wurde erfolgreich beendet.
timeout /t 3 > nul
