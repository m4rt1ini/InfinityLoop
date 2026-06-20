import os
import subprocess

# Create dummy video with tone
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=30", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264", "-c:a", "pcm_s16le", "test_base.mkv"], check=True)

# Concat
with open("list.txt", "w") as f:
    f.write("file 'test_base.mkv'\n")
    f.write("file 'test_base.mkv'\n")

# To MP4
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c:v", "copy", "-c:a", "aac", "test_out.mp4"], check=True)

print("SUCCESS")
