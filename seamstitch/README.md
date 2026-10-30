# seamstitch

Joins clips that are meant to read as one continuous shot, correcting only a
short window either side of each cut. Everything outside that window is left
untouched, so clips that legitimately differ from one another are not dragged
towards a common look.

    python3 -m seamstitch config.json

## Config

```json
{
  "output": "stitched.mp4",
  "clips": ["a.mp4", "b.mp4", "c.mp4"],
  "junctions": ["stitch", "cut"],
  "options": {"window_seconds": 1.25},
  "encode": {"crf": 18, "preset": "slow"}
}
```

Paths are relative to the config file. `junctions` has one entry per gap:
`stitch` corrects the seam, `cut` concatenates untouched (use it wherever a
transition or a genuine change of shot belongs). Omit it to stitch everywhere.

`--dry-run` measures and prints the report without rendering. `--verify`
measures the rendered file afterwards and reports what actually landed at each
seam. `--report FILE` also writes the report out. `--keep-work` leaves the
generated window frames on disk.

## Interface

    python3 -m seamstitch.ui --dir /path/to/clips

Serves a page on http://127.0.0.1:8765 for picking clips from a folder,
ordering them, and choosing per gap whether to stitch or leave a plain cut.
Each gap shows the two frames that would meet there. Measure-only and render
both run through the same code as the command line, and the report, including
verification, appears in the panel.

## What a stitch does

Per junction, measured on both sides and applied as a ramp that is full at the
cut and zero at the window edge:

- **frame pair** — the most similar tail/head pair, trimming overlap if that
  beats the natural join by a clear margin. Below `min_match` the clips are
  reported as unrelated and the junction is left alone.
- **exposure and contrast** — per channel, each side moving half way to the
  other. Levels are read off a linear fit through the window rather than a flat
  average, so a clip whose exposure is already drifting still matches at the
  cut itself.
- **sharpness** — the crisper side is blurred down to the softer one, measured
  after the geometric correction so the zoom's own softening is accounted for.
  Nothing is ever sharpened.
- **registration** — the scale and pan offset between the two frames at the cut.
- **camera speed** — both sides ramp to a shared rate at the cut, so the motion
  does not stop or jump there.

The last two share one cubic envelope per axis: zero value and zero slope at
the window edge, the shared rate at the cut. Ramping to that rate necessarily
accumulates some zoom, and the envelope takes the smallest amount that does not
send the picture the other way first.

## Framing reserve

Zooming out inside a window needs picture beyond the frame edge, which only a
clip with spare resolution has. The registration correction is therefore
allocated in proportion to each clip's headroom, so a clip already at output
resolution is never cropped and upscaled along its whole length for it. When a
reserve is unavoidable it is reported; when the zoom budget cannot be met the
window is shortened and that is reported too.

## Verification

`--verify` re-measures the rendered file at every seam: whether the motion rate
at the cut sits inside the range of its neighbours, how much registration is
left, and whether exposure, contrast and sharpness step by more than the
sequence normally moves between frames. Window edges are checked the same way.
Anything outside tolerance is marked for review rather than silently accepted.

## Limits

- All clips must share a frame rate.
- Motion is modelled as zoom plus pan about the frame centre. Rotation and
  parallax are not handled.
- Audio is concatenated with a short fade either side of a stitched cut; video
  frame counts are preserved exactly, so sync is unaffected.
