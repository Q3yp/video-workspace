"""What each junction measured and what was applied to it."""


def _fmt3(v):
    return "[%.1f %.1f %.1f]" % tuple(v)


def junction_lines(k, j, fps):
    out = ["Junction %d  (%s)" % (k, j.mode)]
    if j.match:
        m = j.match
        out.append("  frame match      best NCC %.4f (natural %.4f)"
                   % (m["best_ncc"], m["natural_ncc"]))
    if j.skipped:
        out.append("  SKIPPED          %s" % j.skipped)
        return out
    me = j.meas
    ra, rb = me["rate_a"], me["rate_b"]
    ss, sdx, sdy = me["seam"]
    out += [
        "  window           %.2fs (%d frames each side)"
        % (me["window_frames"] / fps, me["window_frames"]),
        "  motion rate      A %+.2f permille/f  B %+.2f  -> target %+.2f"
        % (ra[0], rb[0], me["target_rate"]),
        "  pan rate         A (%+.2f, %+.2f) px/f  B (%+.2f, %+.2f)"
        % (ra[1], ra[2], rb[1], rb[2]),
        "  seam step        scale %+.2f permille   shift (%+.2f, %+.2f) px  quality %.3f"
        % (ss, sdx, sdy, me["seam_quality"]),
        "  zoom applied     A %+.1f..%+.1f permille   B %+.1f..%+.1f"
        % (j.a_scale.min(), j.a_scale.max(), j.b_scale.min(), j.b_scale.max()),
        "  framing reserve  A %.1f permille   B %.1f"
        % (me["reserve"][0], me["reserve"][1]),
    ]
    ea, eb, et = me["sharpness"]
    out.append("  sharpness        A %.2f  B %.2f  -> %.2f   blur A %.2f  B %.2f"
               % (ea, eb, et, j.a_sigma.max(), j.b_sigma.max()))
    ma, sda = me["color_a"]
    mb, sdb = me["color_b"]
    out.append("  colour mean      A %s  B %s" % (_fmt3(ma), _fmt3(mb)))
    out.append("  colour spread    A %s  B %s" % (_fmt3(sda), _fmt3(sdb)))
    for n in j.notes:
        out.append("  note             %s" % n)
    return out


def render_report(infos, junctions, layouts, out_w, out_h, fps, total_frames):
    lines = ["Output %dx%d @ %g fps, %d frames (%.2fs)"
             % (out_w, out_h, fps, total_frames, total_frames / fps), ""]
    for i, (info, l) in enumerate(zip(infos, layouts)):
        lines.append("Clip %d  %s" % (i, info["path"]))
        lines.append("  source %dx%d, %d frames; used %d..%d; work size %dx%d"
                     % (info["width"], info["height"], info["frames"],
                        l.start, l.end, l.sw, l.sh))
    lines.append("")
    for k, j in enumerate(junctions):
        lines += junction_lines(k, j, fps)
        lines.append("")
    return "\n".join(lines)
