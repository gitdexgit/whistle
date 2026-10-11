import os
import re
import wave
import subprocess
import numpy as np
import needle

pipe_path = "/dev/shm/whistle.pipe"

if os.path.exists(pipe_path):
    os.remove(pipe_path)

os.mkfifo(pipe_path)

replacements = {
    r"\bpseudo\b": "sudo",
    r"\bpac man\b": "pacman",
    r"\bi three\b": "i3",
    r"\bnew line\b": "\n",
}

def load_trimmed(path, threshold=0.015):
    with wave.open(path, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    active = np.where(np.abs(audio) > threshold)[0]
    if len(active) == 0:
        return None
    start = max(0, active[0] - 1600)
    end = min(len(audio), active[-1] + 1600)
    return audio[start:end]

def split_on_pauses(audio, sample_rate=16000, threshold=0.015, min_pause=0.3):
    if len(audio) <= sample_rate * 4:
        return [audio]

    silent = np.abs(audio) < threshold
    pause_samples = int(min_pause * sample_rate)
    chunks = []
    start = 0
    count = 0
    cut_point = None

    for idx, is_silent in enumerate(silent):
        if is_silent:
            count += 1
            if count >= pause_samples:
                cut_point = idx - (count // 2)
        else:
            if cut_point is not None:
                if (cut_point - start) >= sample_rate * 2.5:
                    chunk = audio[start:cut_point]
                    if len(chunk) > 0:
                        chunks.append(chunk)
                    start = cut_point
                cut_point = None
            count = 0

    if start < len(audio):
        chunk = audio[start:]
        if len(chunk) > 0:
            chunks.append(chunk)

    return chunks if chunks else [audio]

while True:
    with open(pipe_path, "r") as pipe:
        for line in pipe:
            path = line.strip()
            if os.path.exists(path):
                audio = load_trimmed(path)
                if audio is None:
                    continue

                chunks = split_on_pauses(audio)
                parts = []

                for chunk in chunks:
                    res = needle.transcribe(chunk, language="en", keywords=["i3", "Arch", "Linux", "dex", "sudo", "pacman"])
                    piece = res["text"].strip()
                    if piece:
                        parts.append(piece)

                text = " ".join(parts).strip()
                for pattern, sub in replacements.items():
                    text = re.sub(pattern, sub, text, flags=re.IGNORECASE)

                if text:
                    subprocess.run(["xdotool", "type", "--delay", "0", "--clearmodifiers", text + " "])
