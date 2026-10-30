"""Turning junction measurements into a windowed correction plan."""
import math

import numpy as np

from . import measure, probe


def hermite(u, p0, m0, p1, m1):
    """Cubic Hermite; m0/m1 are slopes with respect to u."""
    u2, u3 = u * u, u * u * u
    return ((2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0
            + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1)


def smoothstep(u):
    return hermite(u, 0.0, 0.0, 1.0, 0.0)


DEFAULTS = {
    "window_seconds": 1.25,
    "window_seconds_max": 2.0,
    "window_seconds_min": 0.25,
    "rate_split": 0.5,        # 0 = correct clip B only, 1 = correct clip A only
    "max_upscale_permille": 95.0,
    "search_frames": 12,      # how far to look for a better matching frame pair
    "trim_margin": 0.002,     # NCC gain required before trimming anything
    "min_match": 0.90,        # below this the clips are not a continuous shot
    "stat_frames": 8,         # frames averaged for colour and sharpness
    "audio_fade_ms": 30.0,
}


class Junction:
    """One correction plan; `a_*` arrays run up to the cut, `b_*` away from it."""

    def __init__(self, index, mode):
        self.index = index
        self.mode = mode
        self.skipped = None
        self.trim_a = 0
        self.trim_b = 0
        self.match = None
        self.notes = []
        self.a_scale = self.a_dx = self.a_dy = None
        self.b_scale = self.b_dx = self.b_dy = None
        self.a_color = self.b_color = None
        self.a_sigma = self.b_sigma = None
        self.meas = {}

    @property
    def window_a(self):
        return 0 if self.a_scale is None else len(self.a_scale)

    @property
    def window_b(self):
        return 0 if self.b_scale is None else len(self.b_scale)


def _analysis_size(out_w, out_h):
    w = max(160, (out_w // 4) // 2 * 2)
    return w, max(90, int(round(w * out_h / out_w)) // 2 * 2)


def _solve_axis(step, rate_a, rate_b, rate_split, residual_split, na, nb):
    """Envelopes that make rate and position continuous across the cut.

    Each side is zero with zero slope at its far edge and reaches the shared
    target rate at the cut. Ramping to that rate necessarily accumulates a
    non-zero value at the cut; taking a third of the end slope is the smallest
    such value that does not send the curve the other way first. Whatever
    registration error is left over is then split between the two sides.
    """
    target = rate_a + (1.0 - rate_split) * (rate_b - rate_a)
    slope_a = (target - rate_a) * (na - 1)
    slope_b = (target - rate_b) * (nb - 1)
    base_a = slope_a / 3.0
    base_b = -slope_b / 3.0
    residual = (target - step) - (base_b - base_a)
    cut_a = base_a - residual_split * residual
    cut_b = base_b + (1.0 - residual_split) * residual
    a = hermite(np.linspace(0.0, 1.0, na), 0.0, 0.0, cut_a, slope_a)
    b = hermite(np.linspace(0.0, 1.0, nb), cut_b, slope_b, 0.0, 0.0)
    return a, b, target


def _headroom_permille(info, out_w, out_h):
    hz = min(info["width"] / out_w, info["height"] / out_h)
    return 1000.0 * math.log(max(hz, 1.0))


def plan_junction(index, info_a, info_b, mode, out_w, out_h, opts, fps):
    o = dict(DEFAULTS)
    o.update(opts or {})
    j = Junction(index, mode)
    if mode != "stitch":
        j.skipped = "mode=%s" % mode
        return j

    aw, ah = _analysis_size(out_w, out_h)
    search = int(o["search_frames"])
    pad = max(int(round(o["window_seconds_max"] * fps)) + 12, 24)

    tail_n = min(info_a["frames"], pad + search)
    head_n = min(info_b["frames"], pad + search)
    a_tail = probe.read_frames(info_a["path"], info_a["frames"] - tail_n, tail_n, aw, ah)
    b_head = probe.read_frames(info_b["path"], 0, head_n, aw, ah)

    ia, jb, best, natural = measure.find_pair(a_tail[-search:], b_head[:search])
    j.match = {"best_ncc": best, "natural_ncc": natural,
               "trim_a": search - 1 - ia, "trim_b": jb}
    if best < o["min_match"]:
        j.skipped = "match %.3f below min_match %.3f: not a continuous shot" % (
            best, o["min_match"])
        return j
    if best - natural > o["trim_margin"]:
        j.trim_a = search - 1 - ia
        j.trim_b = jb
        j.notes.append("trimmed %d frame(s) from A and %d from B (NCC %.4f vs %.4f)"
                       % (j.trim_a, j.trim_b, best, natural))

    a_end = tail_n - j.trim_a          # exclusive index into a_tail
    b_start = j.trim_b
    a_cut = a_tail[:a_end]
    b_cut = b_head[b_start:]

    win = int(round(o["window_seconds"] * fps))
    win = max(2, min(win, a_end - 10, len(b_cut) - 10))

    # Geometry is measured finer than the frame search: one frame's worth of
    # zoom sits near the noise floor at analysis size, and getting the seam
    # step wrong there shows up directly as a jump in the result.
    gw = max(320, (out_w // 2) // 2 * 2)
    gh = max(180, int(round(gw * out_h / out_w)) // 2 * 2)
    geo = 10
    ga = probe.read_frames(info_a["path"], info_a["frames"] - j.trim_a - geo, geo, gw, gh)
    gb = probe.read_frames(info_b["path"], b_start, geo, gw, gh)
    kx, ky = out_w / float(gw), out_h / float(gh)
    ra = measure.motion_rate(ga, at_end=True)
    rb = measure.motion_rate(gb, at_end=False)
    rate_a = (ra[0], ra[1] * kx, ra[2] * ky)
    rate_b = (rb[0], rb[1] * kx, rb[2] * ky)
    step_s, sdx, sdy, q = measure.seam_step(ga[-1], gb[0])
    step_dx, step_dy = sdx * kx, sdy * ky
    j.meas.update({"rate_a": rate_a, "rate_b": rate_b,
                   "seam": (step_s, step_dx, step_dy), "seam_quality": q})

    head_a = _headroom_permille(info_a, out_w, out_h)
    head_b = _headroom_permille(info_b, out_w, out_h)
    split = float(o["rate_split"])
    # A clip with no spare resolution cannot give up framing without being
    # upscaled along its whole length, so let the clip with headroom carry the
    # registration correction.
    rshare = head_a / (head_a + head_b) if (head_a + head_b) > 0 else 0.5

    def solve(step, sdx, sdy, width):
        """Envelopes for one measured seam, shrinking the window if the zoom
        budget cannot be met."""
        notes = []
        while True:
            sa, sb, target = _solve_axis(step, rate_a[0], rate_b[0], split, rshare, width, width)
            dxa, dxb, _ = _solve_axis(sdx, rate_a[1], rate_b[1], split, rshare, width, width)
            dya, dyb, _ = _solve_axis(sdy, rate_a[2], rate_b[2], split, rshare, width, width)
            shift_a = math.log(1.0 + 2.0 * max(abs(dxa).max() / out_w,
                                               abs(dya).max() / out_h)) * 1000.0
            shift_b = math.log(1.0 + 2.0 * max(abs(dxb).max() / out_w,
                                               abs(dyb).max() / out_h)) * 1000.0
            res_a = max(0.0, -float(sa.min())) + shift_a
            res_b = max(0.0, -float(sb.min())) + shift_b
            need_a = res_a + float(sa.max())
            need_b = res_b + float(sb.max())
            ok = (need_a <= head_a + o["max_upscale_permille"]
                  and need_b <= head_b + o["max_upscale_permille"])
            floor = int(round(o["window_seconds_min"] * fps))
            if ok or width <= floor:
                if not ok:
                    notes.append("zoom budget still exceeded at the minimum window "
                                 "(A needs %.1f permille of %.1f, B needs %.1f of %.1f); "
                                 "correction applied anyway"
                                 % (need_a, head_a + o["max_upscale_permille"],
                                    need_b, head_b + o["max_upscale_permille"]))
                return (sa, sb, dxa, dxb, dya, dyb, target, res_a, res_b, width, notes)
            width = max(floor, int(width * 0.8))
            notes.append("window shortened to %.2fs to stay inside the zoom budget"
                         % (width / fps))

    def solve_fixed(step, sdx, sdy, width):
        """The framing reserve is itself a constant zoom on the clip, so the
        seam constraint has to be solved together with it."""
        eff = step
        res = solve(eff, sdx, sdy, width)
        for _ in range(4):
            nxt = step + res[8] - res[7]
            if abs(nxt - eff) < 0.05:
                break
            eff = nxt
            res = solve(eff, sdx, sdy, width)
        return res

    sa, sb, dxa, dxb, dya, dyb, target, reserve_a, reserve_b, win, notes = solve_fixed(
        step_s, step_dx, step_dy, win)

    k = min(int(o["stat_frames"]), win)
    a_rgb = probe.read_frames(info_a["path"], info_a["frames"] - j.trim_a - k, k,
                              aw, ah, gray=False)
    b_rgb = probe.read_frames(info_b["path"], b_start, k, aw, ah, gray=False)
    ma, sda = measure.color_stats(a_rgb, at_end=True)
    mb, sdb = measure.color_stats(b_rgb, at_end=False)
    tgt_m, tgt_s = (ma + mb) / 2.0, (sda + sdb) / 2.0
    j.meas["color_a"] = (ma, sda)
    j.meas["color_b"] = (mb, sdb)
    j.a_color = _color_ramp(ma, sda, tgt_m, tgt_s, win, rising=True)
    j.b_color = _color_ramp(mb, sdb, tgt_m, tgt_s, win, rising=False)

    a_out = probe.read_frames(info_a["path"], info_a["frames"] - j.trim_a - k, k, out_w, out_h)
    b_out = probe.read_frames(info_b["path"], b_start, k, out_w, out_h)
    # Measure each side as it will actually appear at the cut: the zoom ramp
    # softens it, and matching to the unzoomed sharpness leaves a step behind.
    a_at_cut = measure.warp(a_out[-1], math.exp(float(sa[-1]) / 1000.0))
    b_at_cut = measure.warp(b_out[0], math.exp(float(sb[0]) / 1000.0))
    ea = measure.laplacian_energy(a_at_cut)
    eb = measure.laplacian_energy(b_at_cut)
    tgt_e = min(ea, eb)
    j.meas["sharpness"] = (ea, eb, tgt_e)
    sig_a = measure.solve_blur_sigma(a_at_cut, tgt_e) if ea > tgt_e else 0.0
    sig_b = measure.solve_blur_sigma(b_at_cut, tgt_e) if eb > tgt_e else 0.0

    # Second pass: fitting across a colour and sharpness mismatch biases the
    # geometry, so re-measure the seam once both sides look alike.
    ga_m = _apply_flat(ga[-1], j.a_color, -1, sig_a * gw / out_w)
    gb_m = _apply_flat(gb[0], j.b_color, 0, sig_b * gw / out_w)
    s2, dx2, dy2, q2 = measure.seam_step(ga_m, gb_m)
    j.meas["seam_raw"] = (step_s, step_dx, step_dy)
    step_s, step_dx, step_dy, q = s2, dx2 * kx, dy2 * ky, q2
    j.meas["seam"] = (step_s, step_dx, step_dy)
    j.meas["seam_quality"] = q

    sa, sb, dxa, dxb, dya, dyb, target, reserve_a, reserve_b, win2, more = solve_fixed(
        step_s, step_dx, step_dy, win)
    notes += more
    if win2 != win:
        win = win2
        j.a_color = _color_ramp(ma, sda, tgt_m, tgt_s, win, rising=True)
        j.b_color = _color_ramp(mb, sdb, tgt_m, tgt_s, win, rising=False)

    j.a_scale, j.b_scale = sa, sb
    j.a_dx, j.b_dx = dxa, dxb
    j.a_dy, j.b_dy = dya, dyb
    j.a_sigma = sig_a * smoothstep(np.linspace(0.0, 1.0, win))
    j.b_sigma = sig_b * smoothstep(np.linspace(1.0, 0.0, win))
    j.meas["target_rate"] = target
    j.meas["reserve"] = (reserve_a, reserve_b)
    j.meas["window_frames"] = win
    j.notes += notes
    return j


def _apply_flat(gray, color, at, sigma):
    """Colour map and blur applied to a single grey frame, for measurement."""
    gain, offset = color
    out = gray * float(gain[at].mean()) + float(offset[at].mean())
    return measure.blur(out, sigma) if sigma > 0.01 else out


def _color_ramp(mean, std, tgt_mean, tgt_std, n, rising):
    """Per-frame (gain, offset) per channel, identity at the window edge."""
    u = np.linspace(0.0, 1.0, n) if rising else np.linspace(1.0, 0.0, n)
    w = smoothstep(u)[:, None]
    m = mean[None, :] + w * (tgt_mean - mean)[None, :]
    s = std[None, :] + w * (tgt_std - std)[None, :]
    gain = s / np.maximum(std[None, :], 1e-6)
    offset = m - gain * mean[None, :]
    return gain.astype(np.float32), offset.astype(np.float32)
