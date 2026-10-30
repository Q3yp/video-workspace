---
name: video-production
description: Local AI video production, including direction, image and video assets, shots, editing, narration, and post-production.
---

# Video production workspace

Local AI video production. Images come from Codex image generation. Video and audio come from LibTV through `libtv-local` (available on PATH; usage in the `asset-generation` skill). Post-production uses Remotion, HyperFrames and ffmpeg. `seamstitch/` joins clips that must read as one continuous shot; see `seamstitch/README.md`.

This file holds the rules every part of the work needs. The files beside it hold the guidelines for one stage, genre, model or client; read the ones the work in hand touches. Each film lives in its own folder, and its own `AGENTS.md` holds only what these files do not cover, overriding them where they differ. A correction that comes out of a film is written, as a rule, into the most general file it holds for.

## Guidelines

| File | Covers |
|---|---|
| `direction.md` | Steps 1 to 3: brief, research, story, plot, shot split, durations, generation/post split, references per shot |
| `assets.md` | Steps 4 to 6: asset list, asset prompt files, image prompts, editing an image, review |
| `shots.md` | Steps 7 and 8: shot prompts, generation, take review |
| `post.md` | Step 9: edit, graphics, narration, sound, versions and review |
| `genres.md` | Company films, and what each genre changes: brand film, motion graphics |
| `models.md` | How to drive each model: Codex image generation, MiniMax H3, Seedance 2.x, MiniMax Speech |

Client-specific facts and approved material belong in a private client file linked from the film's own instructions.

A film's genre and client are recorded in the brief of its `01-director/plot.md`, or in its `AGENTS.md`.

## Production order

1. **Plot.** Built to the standard of the film's genre.
2. **Director script.** Shot by shot: what the viewer sees and hears, duration, and how each shot joins the next.
3. **Generation/post split.** Decide, per shot and per element, what the video model generates and what post-production adds. The split changes the asset list and the shot prompts, so it happens before either is written.
4. **Asset list.** Every environment, character, object, state change and keyframe the shots need, collected from the References column of the shot table.
5. **Asset prompt file and batch generation.**
6. **Asset review** before any video is generated.
7. **Shot prompts.** One per generated shot.
8. **Video generation and take review** through `libtv-local`.
9. **Post and assembly.** Graphics, transitions, narration, sound, grade, final encode.

## Roles

The director writes the plot, the script and every prompt, reviews every asset and take, and builds the on-screen graphics itself, directly, without writing a spec first. A generating agent runs the asset prompt files: it finds the real photographs a file names and generates the images, and leaves judging them to the director, because an agent that judges its own images repairs them edit after edit until the texture is destroyed. `models.md` names the generating agent and how to hand it a file.

Work moves to another agent only when the user asks. The on-screen graphics and motion design stay with the director unless the user hands those over by name.

## Prompting

Every prompt follows one rule, including instructions written for an agent such as this file or a task brief: write only what the reader would not get right by itself, say it once, and at the strength you want. A photograph already has photographic texture, and a reference already carries its face, skin, clothing, surfaces and light; restating or overstating them makes the model exaggerate them, and a list of details can contradict the texture a real photograph would have. Instructions state the rule without citing tests or giving examples.

A prompt does need the subject and what it is doing, the layout, the light, the camera, what changes from a reference, and anything the model would plausibly get wrong unless told. A plain line on the feeling of the moment is fine. Polish words such as cinematic, epic, premium, dramatic, anamorphic, 8K and hyper-detailed are not, because the model trades realism for them.

## References

Video generation is always reference-to-video: the references carry identity and look, and the prompt arranges them and directs what they do. This keeps characters and scenes consistent across shots and lets one asset serve many shots.

Reference kinds:

- **Environment**: a location on its own, without the cast.
- **Character**: one character per image, on a plain or neutral background. A turnaround sheet with several angles is fine.
- **Object**: one product or prop per image, with any text or logo on it clearly legible.
- **State**: a changed object, a new action pose or a character's expression is a standalone reference of its own. A transformation is shown by giving the model both states, not by a keyframe.
- **Keyframe**: a composed frame for complex motion or a complex scene that the other references cannot describe. Use it for nothing else, because a keyframe ties the asset to one shot.

A reference matches the scale of the shot that uses it, because the model invents whatever a reference shows too small. Make separate character sheets for face, full body and hands when shots need them, and give a close-up a reference at its own scale. When the close-up is part of a moving shot, its reference either matches the subject's pose, angle and position at that point of the move, or is a pure reference on a plain background with no environment.

The model keeps a reference's layout and starts the shot from the state the reference shows:

- **Lay out the mechanism where the action must land.** Where a nozzle points, where a lane leads and where a machine stands decide where the action goes in the shot.
- **Show the state the shot starts from, or a neutral one.** A reference that already shows the end of an action makes the action play backwards.
- **Leave moving matter out.** Spray, smoke and splashing start inside the shot from a reference that shows none of them, so the model draws them moving rather than as a still mist.

Text and logos generate to high fidelity when a reference shows them clearly. Put them in the object or environment reference rather than leaving them for post.

## Project layout

```
<project>/
  AGENTS.md         only what the workspace files do not cover
  01-director/      plot, director script, production sheet of the cut
  02-assets/
    environment/
    character/
    object/         includes state references
    keyframe/
    sources-real/   real photographs used as references, with SOURCES.md
  03-prompts/       asset prompt files, and shot prompts in shots/
  04-generated/     raw model outputs, named by shot and take
  05-post/          Remotion, HyperFrames and ffmpeg sources, overlays, audio
  06-output/        numbered renders
```

The existing film folders keep their own layouts; new films use this one.
