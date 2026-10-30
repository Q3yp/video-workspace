"""Config in, one video plus a report out."""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from . import plan, probe, render, report, verify


def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    clips = cfg["clips"]
    if len(clips) < 2:
        raise SystemExit("need at least two clips")
    modes = cfg.get("junctions") or ["stitch"] * (len(clips) - 1)
    modes = [m["mode"] if isinstance(m, dict) else m for m in modes]
    if len(modes) != len(clips) - 1:
        raise SystemExit("expected %d junction entries, got %d"
                         % (len(clips) - 1, len(modes)))
    base = os.path.dirname(os.path.abspath(path))
    clips = [c if os.path.isabs(c) else os.path.join(base, c) for c in clips]
    out = cfg.get("output", "stitched.mp4")
    if not os.path.isabs(out):
        out = os.path.join(base, out)
    return clips, modes, out, cfg.get("options", {}), cfg.get("encode", {})


def run_job(paths, modes, out_path, opts, enc, do_verify=False, dry=False,
            keep_work=False, log=print):
    """Measure, report, render, verify. Shared by the command line and the UI."""
    infos = [probe.probe(p) for p in paths]
    fps = infos[0]["fps"]
    for i in infos[1:]:
        if abs(i["fps"] - fps) > 1e-6:
            raise ValueError("clips differ in frame rate (%g vs %g); conform them first"
                             % (fps, i["fps"]))
    out_w = opts.get("width") or min(i["width"] for i in infos)
    out_h = opts.get("height") or min(i["height"] for i in infos)

    junctions = [plan.plan_junction(k, infos[k], infos[k + 1], modes[k],
                                    out_w, out_h, opts, fps)
                 for k in range(len(infos) - 1)]
    layouts = render.build_layouts(infos, junctions, out_w, out_h)
    total = sum(l.end - l.start for l in layouts)
    log(report.render_report(infos, junctions, layouts, out_w, out_h, fps, total))
    if dry:
        return

    work = tempfile.mkdtemp(prefix="seamstitch_")
    try:
        dirs = render.materialise_windows(infos, junctions, layouts, work)
        cmd = render.build_command(
            infos, junctions, layouts, dirs, out_w, out_h, fps, out_path,
            float(opts.get("audio_fade_ms", plan.DEFAULTS["audio_fade_ms"])),
            int(enc.get("crf", 18)), enc.get("preset", "slow"))
        if subprocess.run(cmd).returncode != 0:
            raise RuntimeError("ffmpeg failed")
    finally:
        if keep_work:
            log("work dir kept at %s" % work)
        else:
            subprocess.run(["rm", "-rf", work])
    log("\nwrote %s" % out_path)
    if do_verify:
        log("\n" + verify.format_results(
            verify.verify(out_path, junctions, layouts, out_w, out_h)))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="seamstitch")
    ap.add_argument("config")
    ap.add_argument("--report", help="also write the report here")
    ap.add_argument("--dry-run", action="store_true",
                    help="measure and report, render nothing")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="measure the rendered file and report what landed")
    args = ap.parse_args(argv)

    paths, modes, out_path, opts, enc = load_config(args.config)
    lines = []

    def log(text):
        print(text)
        lines.append(text)

    try:
        run_job(paths, modes, out_path, opts, enc, do_verify=args.verify,
                dry=args.dry_run, keep_work=args.keep_work, log=log)
    except (ValueError, RuntimeError) as e:
        raise SystemExit(str(e))
    if args.report:
        with open(args.report, "w") as f:
            f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
