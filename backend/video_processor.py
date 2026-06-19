import os
import subprocess
import tempfile

def get_video_duration(input_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", input_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0

def get_best_encoder(target_codec="h264"):
    if target_codec == "h264":
        nvenc_codec = "h264_nvenc"
        mac_codec = "h264_videotoolbox"
        cpu_codec = "libx264"
        nvenc_args = ["-preset", "p4", "-cq", "20", "-b:v", "0", "-pix_fmt", "yuv420p"]
        mac_args = ["-q:v", "60", "-pix_fmt", "yuv420p"]
        cpu_args = ["-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p"]
    elif target_codec == "hevc":
        nvenc_codec = "hevc_nvenc"
        mac_codec = "hevc_videotoolbox"
        cpu_codec = "libx265"
        nvenc_args = ["-preset", "p4", "-cq", "25", "-b:v", "0", "-pix_fmt", "yuv420p"]
        mac_args = ["-q:v", "60", "-pix_fmt", "yuv420p"]
        cpu_args = ["-preset", "fast", "-crf", "25", "-pix_fmt", "yuv420p"]
    elif target_codec == "av1":
        nvenc_codec = "av1_nvenc"
        mac_codec = "av1_videotoolbox" 
        cpu_codec = "libsvtav1"
        nvenc_args = ["-preset", "p4", "-cq", "30", "-b:v", "0", "-pix_fmt", "yuv420p"]
        mac_args = ["-q:v", "60", "-pix_fmt", "yuv420p"]
        cpu_args = ["-preset", "8", "-crf", "30", "-pix_fmt", "yuv420p"]
    else:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p"]

    try:
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "nullsrc=s=256x256:d=0.1", "-c:v", nvenc_codec, "-f", "null", "-"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ["-c:v", nvenc_codec] + nvenc_args
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "nullsrc=s=256x256:d=0.1", "-c:v", mac_codec, "-f", "null", "-"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ["-c:v", mac_codec] + mac_args
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return ["-c:v", cpu_codec] + cpu_args

def process_video(input_path, output_path, mode, loops, crossfade_duration=1.0, audio_offset=0.0, codec="h264", progress_callback=None):
    audio_offset = float(audio_offset)
    wrapped_input = None
    encoder_args = get_best_encoder(codec)
    
    orig_duration = get_video_duration(input_path)
    
    def run_ffmpeg(cmd, stage_name, total_dur):
        if progress_callback: progress_callback(0, stage_name)
        cmd_prog = cmd[:1] + ["-progress", "-", "-nostats"] + cmd[1:]
        proc = subprocess.Popen(cmd_prog, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True)
        for line in proc.stdout:
            if "out_time_us=" in line:
                try:
                    tus = int(line.strip().split("=")[1])
                    if total_dur > 0 and tus > 0:
                        prog = min(99, int((tus / 1000000.0) / total_dur * 100))
                        if progress_callback: progress_callback(prog, stage_name)
                except:
                    pass
        proc.wait()
        if proc.returncode != 0:
            raise Exception(f"FFmpeg Error in {stage_name}")

    needs_pre_wrap = (audio_offset > 0.0) and (mode != "crossdissolve")
    if needs_pre_wrap:
        if orig_duration > audio_offset:
            wrapped_input = tempfile.mktemp(suffix=".mp4")
            filter_str = (
                f"[0:a]atrim=start={audio_offset},asetpts=PTS-STARTPTS[a1]; "
                f"[0:a]atrim=end={audio_offset},asetpts=PTS-STARTPTS[a2]; "
                f"[a1][a2]concat=n=2:v=0:a=1[aout]"
            )
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-filter_complex", filter_str,
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", wrapped_input
            ]
            run_ffmpeg(cmd, "Audiospur asynchron zerschneiden...", orig_duration)
            input_path = wrapped_input

    try:
        if mode == "hardcut":
            total_dur = orig_duration * loops
            list_file_path = tempfile.mktemp(suffix=".txt")
            with open(list_file_path, "w", encoding="utf-8") as f:
                for _ in range(loops):
                    f.write(f"file '{os.path.abspath(input_path).replace(chr(92), '/')}'\\n")
            
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", list_file_path, "-c", "copy", output_path
            ]
            run_ffmpeg(cmd, "Kopiere Hardcut Loop...", total_dur)
            os.remove(list_file_path)
            
        elif mode == "pingpong":
            rev_path = tempfile.mktemp(suffix=".mp4")
            cmd_ping = [
                "ffmpeg", "-y", "-i", input_path,
                "-filter_complex", "[0:v]reverse[v];[0:a]anull[a]",
                "-map", "[v]", "-map", "[a]"
            ] + encoder_args + ["-c:a", "aac", rev_path]
            run_ffmpeg(cmd_ping, "Rendere Rückwärts-Sequenz...", orig_duration)
            
            total_dur = orig_duration * loops * 2
            list_file_path = tempfile.mktemp(suffix=".txt")
            with open(list_file_path, "w", encoding="utf-8") as f:
                for _ in range(loops):
                    f.write(f"file '{os.path.abspath(input_path).replace(chr(92), '/')}'\\n")
                    f.write(f"file '{os.path.abspath(rev_path).replace(chr(92), '/')}'\\n")
                    
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", list_file_path, "-c", "copy", output_path
            ]
            run_ffmpeg(cmd, "Setze Ping-Pong Loop zusammen...", total_dur)
            os.remove(list_file_path)
            try:
                os.remove(rev_path)
            except:
                pass
                
        elif mode == "crossdissolve":
            duration = orig_duration
            if duration > 0:
                crossfade_duration = min(float(crossfade_duration), duration / 2.0)
            
            if loops <= 1 and audio_offset == 0.0:
                cmd = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path]
                run_ffmpeg(cmd, "Kopiere Originalvideo...", duration)
                return output_path
                
            T = duration / 2.0
            seamless_base = tempfile.mktemp(suffix=".mkv")
            
            offset_val = T - crossfade_duration
            base_dur = duration - crossfade_duration
            
            filter_str = (
                f"[0:v]setpts=PTS-STARTPTS,trim=start={T}:end={duration},setpts=PTS-STARTPTS[v2]; "
                f"[0:v]setpts=PTS-STARTPTS,trim=start=0:end={T},setpts=PTS-STARTPTS[v1]; "
                f"[v2][v1]xfade=transition=fade:duration={crossfade_duration}:offset={offset_val}[vout]; "
                
                f"[0:a]asetpts=PTS-STARTPTS,atrim=start={T}:end={duration},asetpts=PTS-STARTPTS[a2]; "
                f"[0:a]asetpts=PTS-STARTPTS,atrim=start=0:end={T},asetpts=PTS-STARTPTS[a1]; "
                f"[a2][a1]acrossfade=d={crossfade_duration}[aout]"
            )
            
            cmd_base = [
                "ffmpeg", "-y", "-i", input_path,
                "-filter_complex", filter_str,
                "-map", "[vout]", "-map", "[aout]"
            ] + encoder_args + ["-c:a", "pcm_s16le", seamless_base]
            
            run_ffmpeg(cmd_base, "Generiere Seamless Base Block...", base_dur)
            
            total_dur = base_dur * loops
            
            import math
            list_file_path = tempfile.mktemp(suffix=".txt")
            
            if audio_offset > 0.0:
                extra_loops = math.ceil(audio_offset / base_dur) if base_dur > 0 else 1
                aud_loops = loops + extra_loops
                total_concat_loops = aud_loops
            else:
                total_concat_loops = loops
                
            with open(list_file_path, "w", encoding="utf-8") as f:
                for _ in range(total_concat_loops):
                    f.write(f"file '{os.path.abspath(seamless_base).replace(chr(92), '/')}'\n")
            
            if audio_offset > 0.0:
                cmd_final = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", list_file_path,
                    "-filter_complex", f"[0:a]atrim=start={audio_offset}:end={audio_offset + total_dur},asetpts=PTS-STARTPTS[aout]",
                    "-map", "0:v", "-map", "[aout]",
                    "-t", str(total_dur),
                    "-c:v", "copy", "-c:a", "aac", output_path
                ]
                run_ffmpeg(cmd_final, "Setze Loops und Audio-Offset zusammen...", total_dur)
            else:
                cmd_final = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", list_file_path, "-c", "copy", output_path
                ]
                run_ffmpeg(cmd_final, "Kopiere Seamless Loops...", total_dur)
                
            os.remove(list_file_path)
            try:
                os.remove(seamless_base)
            except:
                pass
            
    finally:
        if wrapped_input and os.path.exists(wrapped_input):
            try:
                os.remove(wrapped_input)
            except Exception:
                pass
            
    return output_path
