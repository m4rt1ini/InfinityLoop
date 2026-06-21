import shutil
import os
import tempfile
import subprocess
import sys
import uuid
import asyncio
import threading
import time
import uvicorn
import webview
from fastapi import FastAPI, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from video_processor import process_video

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks = {}

@app.get("/select-input")
def select_input(lang: str = "de"):
    title = "Select Source Video" if lang == "en" else "Eingabevideo waehlen"
    script = f"""import tkinter as tk
from tkinter import filedialog
import sys
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
path = filedialog.askopenfilename(filetypes=[('Video', '*.mp4 *.mov *.avi *.mkv *.webm')], title='{title}')
root.destroy()
sys.stdout.write(path)"""
    try:
        path = subprocess.check_output([sys.executable, "-c", script], text=True)
        return {"path": path}
    except Exception as e:
        return {"error": str(e)}

@app.get("/select-path")
def select_path(lang: str = "de"):
    title = "Select Output Location" if lang == "en" else "Speicherort waehlen"
    script = f"""import tkinter as tk
from tkinter import filedialog
import sys
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
path = filedialog.asksaveasfilename(defaultextension='.mp4', filetypes=[('MP4 Video', '*.mp4')], title='{title}')
root.destroy()
sys.stdout.write(path)"""
    try:
        path = subprocess.check_output([sys.executable, "-c", script], text=True)
        return {"path": path}
    except Exception as e:
        return {"error": str(e)}

@app.post("/process")
async def process_video_endpoint(
    background_tasks: BackgroundTasks,
    input_path: str = Form(...),
    output_path: str = Form(...),
    mode: str = Form(...),
    loops: int = Form(1),
    crossfade_duration: float = Form(1.0),
    audio_offset: float = Form(0.0),
    codec: str = Form("h264"),
    audio_curve: str = Form("qsin")
):
    if not input_path or not os.path.exists(input_path):
        return {"error": "Eingabedatei wurde nicht gefunden."}
    if not output_path:
        return {"error": "Kein Speicherort ausgewaehlt."}

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"progress": 0, "status": "Initialisiere FFmpeg..."}

    def run_task():
        try:
            def on_progress(p, s):
                tasks[task_id]["progress"] = p
                if s: tasks[task_id]["status"] = s

            process_video(input_path, output_path, mode, loops, crossfade_duration, audio_offset, codec, audio_curve, on_progress)
            tasks[task_id]["progress"] = 100
            tasks[task_id]["status"] = "Abgeschlossen!"
        except Exception as e:
            tasks[task_id]["error"] = str(e)

    background_tasks.add_task(run_task)
    return {"status": "success", "task_id": task_id}

@app.get("/progress/{task_id}")
async def get_progress(task_id: str, request: Request):
    async def event_generator():
        last_progress = -1
        while True:
            if await request.is_disconnected():
                break
            if task_id in tasks:
                progress = tasks[task_id].get("progress", 0)
                status = tasks[task_id].get("status", "Warten...")
                error = tasks[task_id].get("error", None)
                
                if error:
                    yield f"event: error\ndata: {error}\n\n"
                    break
                    
                if progress != last_progress or progress == 100:
                    yield f"data: {{\"progress\": {progress}, \"status\": \"{status}\"}}\n\n"
                    last_progress = progress
                    
                if progress >= 100:
                    yield f"event: done\ndata: Fertig\n\n"
                    break
            await asyncio.sleep(0.2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Frontend als statische Dateien mounten
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    # Server im Hintergrund-Thread starten
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    # Kurz warten, bis der Server laeuft
    time.sleep(0.5)
    
    # Natives Desktop-Fenster mit pywebview erzeugen
    window = webview.create_window(
        "InfinityLoop Generator",
        "http://127.0.0.1:8000",
        width=1000,
        height=850,
        background_color='#0f172a'
    )
    webview.start()
