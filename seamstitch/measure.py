"""Measurements taken on either side of a junction."""
import numpy as np


# ---------- geometry ----------

def warp(img, scale, dx=0.0, dy=0.0):
    """Zoom about the centre by `scale`, then shift by (dx, dy) pixels.

    Identity parameters return the image untouched, so a zeroed correction
    envelope leaves window frames bit-identical to the untouched body.
    """
    if scale == 1.0 and dx == 0.0 and dy == 0.0:
        return img
    h, w = img.shape[:2]
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sy = cy + (yy - cy - dy) / scale
    sx = cx + (xx - cx - dx) / scale
    y0 = np.clip(np.floor(sy), 0, h - 2).astype(np.int32)
    x0 = np.clip(np.floor(sx), 0, w - 2).astype(np.int32)
    fy = (sy - y0)[..., None] if img.ndim == 3 else (sy - y0)
    fx = (sx - x0)[..., None] if img.ndim == 3 else (sx - x0)
    return (img[y0, x0] * (1 - fy) * (1 - fx) + img[y0 + 1, x0] * fy * (1 - fx)
            + img[y0, x0 + 1] * (1 - fy) * fx + img[y0 + 1, x0 + 1] * fy * fx)


def _phase_peak(a, b, window):
    aw = (a - a.mean()) * window
    bw = (b - b.mean()) * window
    A = np.fft.rfft2(aw)
    B = np.fft.rfft2(bw)
    # Normalised: warping changes the image energy, so an unnormalised peak
    # would rank scales by how much energy they retain, not by alignment.
    denom = np.linalg.norm(aw) * np.linalg.norm(bw)
    c = np.fft.irfft2(A * np.conj(B), s=a.shape) / max(denom, 1e-9)
    k = np.unravel_index(c.argmax(), c.shape)
    h, w = a.shape

    def sub(v0, vm, vp):
        den = vm - 2 * v0 + vp
        return float(np.clip((vm - vp) / (2 * den), -1, 1)) if den != 0 else 0.0

    dy = k[0] + sub(c[k], c[(k[0] - 1) % h, k[1]], c[(k[0] + 1) % h, k[1]])
    dx = k[1] + sub(c[k], c[k[0], (k[1] - 1) % w], c[k[0], (k[1] + 1) % w])
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    # Negated so the shift reads the same way round as the scale: what has to
    # be applied to `a` to land on `b`, not where `b` sits relative to `a`.
    return -dx, -dy, float(c[k])


def fit_transform(a, b, lo=-0.02, hi=0.06, passes=4, per_pass=9):
    """Best (log-scale, dx, dy) taking frame `a` to frame `b`.

    Coarse-to-fine over scale; translation solved in closed form at each
    scale by phase correlation. Returns log-scale in per-mille.
    """
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    best = None
    for _ in range(passes):
        for lg in np.linspace(lo, hi, per_pass):
            dx, dy, peak = _phase_peak(warp(a, float(np.exp(lg))), b, window)
            if best is None or peak > best[3]:
                best = (float(lg), dx, dy, peak)
        span = (hi - lo) / (per_pass - 1)
        lo, hi = best[0] - span, best[0] + span
    return best[0] * 1000.0, best[1], best[2], best[3]


def motion_rate(frames, at_end, spans=(4, 6, 8)):
    """Per-frame (log-scale permille, dx, dy) motion near a clip boundary."""
    out = []
    for s in spans:
        if len(frames) <= s:
            continue
        i, j = (len(frames) - 1 - s, len(frames) - 1) if at_end else (0, s)
        lg, dx, dy, _ = fit_transform(frames[i], frames[j])
        out.append((lg / s, dx / s, dy / s))
    if not out:
        raise ValueError("not enough frames to measure motion")
    a = np.array(out)
    return tuple(float(v) for v in np.median(a, axis=0))


def seam_step(a_last, b_first):
    lg, dx, dy, q = fit_transform(a_last, b_first)
    return lg, dx, dy, q


# ---------- appearance ----------

def color_stats(frames_rgb, at_end):
    """Per-channel level and spread at the cut.

    A clip whose exposure is drifting would be mismatched by a plain average
    over the window, so fit the trend across the sampled frames and read it off
    at the frame that actually touches the cut.
    """
    f = frames_rgb.reshape(len(frames_rgb), -1, 3)
    means = f.mean(axis=1)
    stds = f.std(axis=1)
    n = len(frames_rgb)
    if n < 3:
        return means.mean(axis=0), stds.mean(axis=0)
    x = np.arange(n, dtype=np.float64)
    at = n - 1 if at_end else 0
    out = []
    for series in (means, stds):
        fit = np.polyfit(x, series, 1)
        out.append(np.polyval(fit, at))
    return out[0], out[1]


def laplacian_energy(gray):
    x = gray
    lap = (x[1:-1, 1:-1] * 4 - x[:-2, 1:-1] - x[2:, 1:-1]
           - x[1:-1, :-2] - x[1:-1, 2:])
    return float(lap.std())


def gaussian_kernel(sigma):
    r = max(1, int(np.ceil(3 * sigma)))
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-(x ** 2) / (2 * sigma ** 2))
    return k / k.sum()


def blur(img, sigma):
    if sigma <= 0.01:
        return img
    k = gaussian_kernel(sigma)
    r = len(k) // 2
    out = np.zeros_like(img, dtype=np.float32)
    pad = [(r, r), (r, r)] + ([(0, 0)] if img.ndim == 3 else [])
    p = np.pad(img, pad, mode="edge")
    for i, w in enumerate(k):
        out += w * p[i:i + img.shape[0], r:r + img.shape[1]]
    p = np.pad(out, pad, mode="edge")
    out = np.zeros_like(out)
    for i, w in enumerate(k):
        out += w * p[r:r + img.shape[0], i:i + img.shape[1]]
    return out


def solve_blur_sigma(gray, target_energy, candidates=None):
    """Smallest blur that brings `gray` down to `target_energy`."""
    if candidates is None:
        candidates = np.arange(0.0, 2.01, 0.05)
    best, best_err = 0.0, abs(laplacian_energy(gray) - target_energy)
    for s in candidates:
        if s == 0:
            continue
        err = abs(laplacian_energy(blur(gray, float(s))) - target_energy)
        if err < best_err:
            best, best_err = float(s), err
    return best


# ---------- junction search ----------

def find_pair(a_tail, b_head):
    """Most similar frame pair between A's tail and B's head (NCC)."""
    def norm(x):
        x = x.reshape(len(x), -1)
        x = x - x.mean(1, keepdims=True)
        n = np.linalg.norm(x, axis=1, keepdims=True)
        n[n == 0] = 1
        return x / n

    c = norm(a_tail) @ norm(b_head).T
    i, j = np.unravel_index(c.argmax(), c.shape)
    return int(i), int(j), float(c[i, j]), float(c[-1, 0])
