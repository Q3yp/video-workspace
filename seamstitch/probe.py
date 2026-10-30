"""Reading clips: metadata and pixel windows."""
import json
import subprocess

import numpy as np


def run(cmd, stdout=True):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("%s failed:\n%s" % (cmd[0], p.stderr.decode()[-3000:]))
    return p.stdout if stdout else None


def probe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_streams", "-show_format", path])
    d = json.loads(out)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    frames = v.get("nb_frames")
    if frames is None:
        frames = int(round(float(v.get("duration", d["format"]["duration"])) * fps))
    return {
        "path": path,
        "width": int(v["width"]),
        "height": int(v["height"]),
        "fps": fps,
        "frames": int(frames),
        "duration": float(d["format"]["duration"]),
        "has_audio": a is not None,
    }


def read_frames(path, start, count, width, height, gray=True):
    """Decode frames [start, start+count) scaled to width x height.

    Decodes from the head of the file: exact, and fast enough for the clip
    lengths this tool targets. Long-form sources would want keyframe seeking.
    """
    # gbrp, not rgb24: swscale converts YUV differently for the two targets,
    # and the render graph ends in gbrp. Reading the same way keeps a window
    # frame identical to the body frame wherever the correction is identity.
    fmt = "gray" if gray else "gbrp"
    vf = ("select='between(n\\,%d\\,%d)',scale=%d:%d,format=%s"
          % (start, start + count - 1, width, height, fmt))
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf,
               "-fps_mode", "passthrough", "-f", "rawvideo", "-"])
    px = 1 if gray else 3
    n = len(raw) // (width * height * px)
    if n < count:
        raise RuntimeError("wanted %d frames from %s at %d, got %d" % (count, path, start, n))
    arr = np.frombuffer(raw, dtype=np.uint8)[: n * height * width * px]
    if gray:
        return arr.reshape(n, height, width).astype(np.float32)
    planes = arr.reshape(n, 3, height, width)          # G, B, R
    return planes[:, [2, 0, 1]].transpose(0, 2, 3, 1).astype(np.float32)
