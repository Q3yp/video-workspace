"""Applying a plan: corrected window frames, then one ffmpeg assembly."""
import math
import os

import numpy as np
from PIL import Image

from . import measure, probe


def _even(x):
    return int(math.ceil(x)) // 2 * 2


class Layout:
    """Frame ranges and framing reserve for one clip."""

    def __init__(self, info, out_w, out_h):
        self.info = info
        self.start = 0
        self.end = info["frames"]
        self.head_window = 0
        self.tail_window = 0
        self.reserve = 0.0
        self.out_w, self.out_h = out_w, out_h

    def finalise(self):
        z = math.exp(self.reserve / 1000.0)
        # Under a pixel of margin is not worth resampling the whole clip for;
        # edge clamping absorbs a sub-pixel shift invisibly.
        if self.out_w * (z - 1.0) / 2.0 < 1.0:
            z = 1.0
        self.sw = max(self.out_w, _even(self.out_w * z))
        self.sh = max(self.out_h, _even(self.out_h * z))

    @property
    def body(self):
        return self.start + self.head_window, self.end - self.tail_window


def build_layouts(infos, junctions, out_w, out_h):
    lay = [Layout(i, out_w, out_h) for i in infos]
    for k, j in enumerate(junctions):
        if j.skipped:
            continue
        lay[k].end -= j.trim_a
        lay[k + 1].start += j.trim_b
        lay[k].tail_window = j.window_a
        lay[k + 1].head_window = j.window_b
        ra, rb = j.meas["reserve"]
        lay[k].reserve = max(lay[k].reserve, ra)
        lay[k + 1].reserve = max(lay[k + 1].reserve, rb)
    for l in lay:
        l.finalise()
    return lay


def _write_window(path_dir, info, first, count, sw, sh, scale, dx, dy,
                  color, sigma, out_w, out_h):
    os.makedirs(path_dir, exist_ok=True)
    frames = probe.read_frames(info["path"], first, count, sw, sh, gray=False)
    gain, offset = color
    px_x = sw / float(out_w)
    px_y = sh / float(out_h)
    for k in range(count):
        img = frames[k]
        g, o = gain[k][None, None, :], offset[k][None, None, :]
        img = img * g + o
        if sigma[k] > 0.01:
            img = measure.blur(img, float(sigma[k]))
        z = math.exp(scale[k] / 1000.0)
        img = measure.warp(img, z, dx[k] * px_x, dy[k] * px_y)
        Image.fromarray(np.clip(np.rint(img), 0, 255).astype(np.uint8)).save(
            os.path.join(path_dir, "f_%05d.png" % (k + 1)))
    return count


def materialise_windows(infos, junctions, layouts, workdir):
    """Render every stitched window to a PNG sequence; returns dir per side."""
    dirs = {}
    for k, j in enumerate(junctions):
        if j.skipped:
            continue
        la, lb = layouts[k], layouts[k + 1]
        da = os.path.join(workdir, "j%02d_a" % k)
        db = os.path.join(workdir, "j%02d_b" % k)
        _write_window(da, infos[k], la.end - j.window_a, j.window_a,
                      la.sw, la.sh, j.a_scale, j.a_dx, j.a_dy,
                      j.a_color, j.a_sigma, la.out_w, la.out_h)
        _write_window(db, infos[k + 1], lb.start, j.window_b,
                      lb.sw, lb.sh, j.b_scale, j.b_dx, j.b_dy,
                      j.b_color, j.b_sigma, lb.out_w, lb.out_h)
        dirs[k] = (da, db)
    return dirs


def _crop_chain(sw, sh, out_w, out_h):
    """Shared tail for both paths.

    The leading rgb24 pins where YUV to RGB happens, so a body frame and a
    window frame of the same clip go through the same swscale call and land on
    identical pixels wherever the correction is identity.
    """
    head = ""
    if (sw, sh) == (out_w, out_h):
        return head + "setsar=1,format=gbrp"
    return (head + "crop=%d:%d:(%d-%d)/2:(%d-%d)/2,setsar=1,format=gbrp"
            % (out_w, out_h, sw, out_w, sh, out_h))


def build_command(infos, junctions, layouts, dirs, out_w, out_h, fps,
                  out_path, audio_fade_ms, crf, preset):
    cmd = ["ffmpeg", "-v", "error", "-stats"]
    idx = {}
    n = 0
    for i, info in enumerate(infos):
        cmd += ["-i", info["path"]]
        idx[("clip", i)] = n
        n += 1
    for k, (da, db) in sorted(dirs.items()):
        cmd += ["-framerate", "%g" % fps, "-i", os.path.join(da, "f_%05d.png")]
        idx[("a", k)] = n
        n += 1
        cmd += ["-framerate", "%g" % fps, "-i", os.path.join(db, "f_%05d.png")]
        idx[("b", k)] = n
        n += 1

    parts = []
    order = []
    for i, l in enumerate(layouts):
        if i > 0 and (i - 1) in dirs:
            tag = "wb%d" % (i - 1)
            parts.append("[%d:v]%s[%s]" % (idx[("b", i - 1)],
                                           _crop_chain(l.sw, l.sh, out_w, out_h), tag))
            order.append(tag)
        b0, b1 = l.body
        tag = "body%d" % i
        parts.append("[%d:v]select='between(n\\,%d\\,%d)',scale=%d:%d,%s[%s]"
                     % (idx[("clip", i)], b0, b1 - 1, l.sw, l.sh,
                        _crop_chain(l.sw, l.sh, out_w, out_h), tag))
        order.append(tag)
        if i in dirs:
            tag = "wa%d" % i
            parts.append("[%d:v]%s[%s]" % (idx[("a", i)],
                                           _crop_chain(l.sw, l.sh, out_w, out_h), tag))
            order.append(tag)

    parts.append("%sconcat=n=%d:v=1:a=0,setpts=N/%g/TB[v]"
                 % ("".join("[%s]" % t for t in order), len(order), fps))

    atags = []
    fade = audio_fade_ms / 1000.0
    for i, l in enumerate(layouts):
        t0, t1 = l.start / fps, l.end / fps
        dur = t1 - t0
        src = ("[%d:a]atrim=start=%.6f:end=%.6f,asetpts=PTS-STARTPTS,aresample=48000"
               % (idx[("clip", i)], t0, t1)) if l.info["has_audio"] else (
              "anullsrc=r=48000:cl=stereo,atrim=duration=%.6f" % dur)
        chain = [src]
        if i > 0 and (i - 1) in dirs:
            chain.append("afade=t=in:st=0:d=%.4f" % fade)
        if i in dirs:
            chain.append("afade=t=out:st=%.6f:d=%.4f" % (max(dur - fade, 0.0), fade))
        tag = "a%d" % i
        parts.append(",".join(chain) + "[%s]" % tag)
        atags.append(tag)
    parts.append("%sconcat=n=%d:v=0:a=1[a]"
                 % ("".join("[%s]" % t for t in atags), len(atags)))

    cmd += ["-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
            "-pix_fmt", "yuv420p", "-fps_mode", "cfr", "-r", "%g" % fps,
            "-c:a", "aac", "-b:a", "192k", out_path, "-y"]
    return cmd
