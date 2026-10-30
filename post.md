# Post

Step 9 of the production order: build the film from the director script with Remotion, HyperFrames and ffmpeg in `05-post/`, and render each version to `06-output/`. The genre in `genres.md` sets the pace and the graphic system.

## Edit

- A move to black is a fade of about half a second, never a cut to black.
- No frozen or stale hold sits around a transition; the next element starts as the fade lands.
- New material joins existing material seamlessly rather than replacing it.
- A take whose movement runs against its neighbours can be played reversed or mirrored, when every action, hand and piece of text in it still reads right that way.

Keep a production sheet for the cut in `01-director/`: for each shot, the take used, its in-point, its speed, and whether it is reversed or mirrored; under it, a log of what each version changed. Whoever picks up the film next starts from it.

## Graphics

- A graphic on a moving shot is tracked to the picture, point by point, not placed by eye.
- Lay out each overlay from its own shot's composition. A card or panel reused across shots gets its layout and motion from each shot, not from the first one it was designed for.
- When the user supplies a motion reference for a graphic, follow its trajectories as given; change speed or density only.
- Choose type for the film and give each face one job: keywords, labels, large readings, units and IDs. Show the user a specimen of the candidates on real frames before settling it. Monospaced figures suit IDs and units, not large readings.

## Narration and on-screen text

- Narration the user writes is used word for word. Report every line you add or change.
- Narration says what neither the picture nor the labels say. It never reads out a label or tagline already on screen.
- Audition voices on the opening and closing lines, and let the user choose before every line is generated.
- Words set on screen as they are spoken are aligned to the recording by forced alignment and checked against the waveform; each word leaves after it has been said. Automatic transcription mishears names and technical terms, so it does not replace listening.

## Sound

- Measure; don't judge by feel.
- Find beats with librosa and check them against a waveform plotted below 120 Hz; shift the grid if the kicks don't line up. Big moves land on the beat.
- Sound effects are ready-made files, from the HyperFrames library first. None are synthesized, and none are whooshes, swooshes or risers.
- Narration and dialogue are loudest, music ducks under them, and effects sit above the music.
- Deliver at about −16 LUFS integrated with peaks below −4 dBFS, measured with ffmpeg `ebur128` on the exported MP4.

## Versions and review

- Each delivery is a new numbered file in `06-output/`; earlier versions stay. Render a smaller copy beside it for review and sharing.
- To revise one part of a finished cut, render only that part for the user to see, then join it to the last version with ffmpeg. Join the picture by stream copy when the formats match, take the sound from the full mix rather than splicing tracks, and check the join for drift between picture and sound.
- For review, grab frames before and after every cue, plot the waveform, and give the user five timestamps to check on headphones. Don't claim the mix sounds good.
