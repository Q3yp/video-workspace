"""Measuring the rendered file, so the report says what happened, not only
what was asked for."""
import numpy as np

from . import measure, probe

TOLERANCE = {
    "seam_shift_px": 0.5,     # residual registration at the cut
    "seam_scale_slack": 2.0,  # permille the seam may sit outside the local range
    "step_ratio": 2.5,        # a jump this many times the local median is flagged
    "sharpness_ratio": 0.15,  # relative high-frequency mismatch across the cut
}


class Check:
    def __init__(self, name, text, ok):
        self.name, self.text, self.ok = name, text, ok

    def __str__(self):
        return "  [%s] %-18s %s" % ("ok" if self.ok else "??", self.name, self.text)


def seam_indices(layouts):
    out, acc = [], 0
    for k, l in enumerate(layouts):
        acc += l.end - l.start
        if k < len(layouts) - 1:
            out.append(acc - 1)
    return out


def _appearance(frames):
    lum = np.array([f.mean() for f in frames])
    std = np.array([f.std() for f in frames])
    lap = np.array([measure.laplacian_energy(f) for f in frames])
    return lum, std, lap


def _step_check(name, series, at, tol, unit=""):
    """Compare the change across `at` with how much the series normally moves."""
    d = np.abs(np.diff(series))
    local = np.delete(d, at)
    ref = float(np.median(local)) if len(local) else 0.0
    got = float(d[at])
    ok = got <= max(ref * tol["step_ratio"], ref + 0.3)
    return Check(name, "step %.2f%s vs typical %.2f%s" % (got, unit, ref, unit), ok)


def verify(out_path, junctions, layouts, out_w, out_h, span=8):
    info = probe.probe(out_path)
    # Finer than the planning resolution: a single frame's worth of zoom is
    # close to the noise floor at analysis size, and this pass runs once.
    aw = max(320, (out_w // 2) // 2 * 2)
    ah = max(90, int(round(aw * out_h / out_w)) // 2 * 2)
    seams = seam_indices(layouts)
    results = []

    for k, j in enumerate(junctions):
        checks = []
        seam = seams[k]
        if j.skipped:
            results.append((k, seam, [Check("skipped", j.skipped, True)]))
            continue

        lo = max(0, seam - span)
        g = probe.read_frames(out_path, lo, min(2 * span + 2, info["frames"] - lo), aw, ah)
        steps = [measure.fit_transform(g[i], g[i + 1]) for i in range(len(g) - 1)]
        at = seam - lo
        scale = np.array([s[0] for s in steps])
        kx, ky = out_w / float(aw), out_h / float(ah)
        dx = np.array([s[1] for s in steps]) * kx
        dy = np.array([s[2] for s in steps]) * ky

        near = np.delete(scale, at)
        lo_s, hi_s = near.min() - TOLERANCE["seam_scale_slack"], near.max() + TOLERANCE["seam_scale_slack"]
        checks.append(Check("motion rate",
                            "seam %+.2f permille, neighbours %+.2f..%+.2f"
                            % (scale[at], near.min(), near.max()),
                            lo_s <= scale[at] <= hi_s))
        checks.append(Check("registration",
                            "seam shift (%+.2f, %+.2f) px, neighbours max %.2f"
                            % (dx[at], dy[at], max(np.abs(np.delete(dx, at)).max(),
                                                   np.abs(np.delete(dy, at)).max())),
                            max(abs(dx[at]), abs(dy[at])) <= TOLERANCE["seam_shift_px"]))

        f = probe.read_frames(out_path, lo, len(g), out_w, out_h)
        lum, std, lap = _appearance(f)
        checks.append(_step_check("exposure", lum, at, TOLERANCE))
        checks.append(_step_check("contrast", std, at, TOLERANCE))
        rel = abs(lap[at + 1] - lap[at]) / max(lap[at], 1e-6)
        checks.append(Check("sharpness", "seam mismatch %.1f%% (%.2f vs %.2f)"
                            % (rel * 100, lap[at], lap[at + 1]),
                            rel <= TOLERANCE["sharpness_ratio"]))

        for edge, name in ((seam - j.window_a, "window edge A"),
                           (seam + j.window_b, "window edge B")):
            e0 = max(0, edge - 3)
            e = probe.read_frames(out_path, e0, min(7, info["frames"] - e0), out_w, out_h)
            elum, _, elap = _appearance(e)
            checks.append(_step_check(name + " lum", elum, edge - e0, TOLERANCE))
            checks.append(_step_check(name + " sharp", elap, edge - e0, TOLERANCE))
        results.append((k, seam, checks))
    return results


def format_results(results):
    lines = ["Verification of the rendered file"]
    for k, seam, checks in results:
        lines.append("Junction %d at output frame %d" % (k, seam))
        lines += [str(c) for c in checks]
    flagged = sum(1 for _, _, cs in results for c in cs if not c.ok)
    lines.append("%d check(s) flagged for review" % flagged if flagged
                 else "all checks within tolerance")
    return "\n".join(lines)
