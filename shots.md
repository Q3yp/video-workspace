# Shots

Steps 7 and 8 of the production order: write one prompt per generated shot from its row in the director script, generate it, and pass or fail each take before it reaches the edit. What references do to a shot is in `AGENTS.md`; the target model's format, labels and behaviour are in `models.md`. Reference limits, durations and resolutions change between models and versions; read them from `libtv-local models "MODEL DISPLAY NAME" --schema --json` before writing the prompt.

## Shot prompt file

One file per shot in `03-prompts/shots/`, named by shot. At the top: the model and its settings, the generation length and the screen length, and the references in attachment order. Under them, a note for each take that failed: what it got wrong and what the next take changes. Then the draft in the four sections below, then the prompt converted into the model's format.

## Four sections

Draft in this structure, in this order, then convert it as `models.md` describes for the target model.

1. **Reference description.** Label every reference and state what it controls, one role per reference. Name something to leave out only when it could plausibly end up in the shot. When a reference's viewpoint differs from the shot's, say that it controls appearance only and give the shot's own viewpoint. Four or five references usually work better than the model's maximum, because the model weighs fewer inputs more reliably.
2. **Scene setup.** Location, time of day, light, the spatial layout, and where each subject stands relative to the others and to the camera.
3. **Camera.** Shot size, lens, height and movement, plus the opening and closing framing. Put locked-camera and held-frame requirements from post here.
4. **Plot.** Timed beats: who does what, when the referenced content appears, and the sound produced in each beat. The total matches the generation duration.

### Keyframe references

A keyframe goes in as a labeled reference like any other, and the prompt names it. State that it is a keyframe, the moment in the shot it depicts, and the composition it shows, so the model passes through that frame instead of only borrowing its look. Describe the motion into and out of the keyframe in Plot, and refer back to the same label there.

### Writing the action

- **State the start state when an action could be read either way.** Attaching and removing, opening and closing look alike in motion. Say what is in place before the action begins, which way the hands or parts travel, and where things end up.
- **Describe what the viewer sees where something must not happen.** The model tends to make identical devices act alike, and saying that one stays off is weak. Say what stays visible in that part of the frame for the whole shot.
- **Say when moving matter starts,** at a timed beat inside the shot, and how it keeps moving to the end.

### What post needs from the shot

The Post column of the director script says which of these apply:

- **Joined by a transition.** The shot opens and/or closes on a still, held frame of about half a second, so a dissolve or wipe blends two stable images instead of two moving ones.
- **Carries an overlay.** Leave the overlay area empty and say where it is. Lock the camera if the overlay must track the picture.
- **Gets a speed ramp or trim.** Generate longer than the target duration to leave handles.
- **Played reversed.** Describe the opposite change, and keep everything else in the frame still so the reversal does not show.
- **Gets narration or music.** Ask the model only for sound produced inside the scene.

## Generating

Generate through `libtv-local` as the `asset-generation` skill describes. Save each take in `04-generated/<shot>/take<N>/` together with the exact prompt it was generated from.

## Take review

Review every take before it is used, with the same must-hold and has-room split as the asset review in `assets.md`: what this shot's job depends on must hold, and differences a viewer would not notice have room.

- Run ffmpeg `cropdetect` on every take. A model can bake letterbox bars into a 16:9 take. Crop the picture area back to 16:9 in the edit unless the crop loses the subject.
- Check that moving matter actually moves; measure the motion in its region when it is unclear.
- Check that each action reads the way the script means it, that the mechanism lands where it should, and that things turn and travel in the script's direction.
- Check that overlay areas stay empty and that a locked camera stays locked.

Record the verdict in the shot prompt file's take notes. After two or three takes fail on the same point, fix it in post if post can, and otherwise show the user what is still wrong.
