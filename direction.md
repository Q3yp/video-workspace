# Direction

Steps 1 to 3 of the production order: take a brief to a plot and a director script whose shot table is ready for the asset list. The film's genre in `genres.md` sets the standard the plot must meet, and its client file gives the facts and approved assets; apply both from step 1. The reference kinds and what references do to a shot are in `AGENTS.md`.

Write the plot and script in the user's language, with the `conveying` skill.

## 1. Brief

Collect what changes the film:

- Purpose and where it will be shown.
- Genre, from `genres.md`. Settle it with the user before proposing concepts, because it decides what the story is made of as well as the pace, the camera and the look.
- Client.
- Audience.
- Total duration and aspect ratio.
- Language of narration and on-screen text, and any other language versions.
- Facts that must appear: product names, features, figures, people, places.
- Existing assets the film must use.

Take what the user and project files already give. Ask once, in one message, only about gaps that would change the structure or the shot count. If the user wants to proceed without answers, use 60 seconds and 16:9 and say so in the plot.

## 2. Research and concepts

Study the best films in the chosen genre, from any industry as well as the subject's own, and collect facts with sources that the film can stand on. When the user names a reference film, watch it and measure it: the number of cuts and the median shot length, how much of it is graphics, and what carries it from start to end. Write down what this film takes from it.

Choose material whose real events already move at the genre's pace, so the edit follows the story instead of being imposed on it. Propose two or three concepts with a recommendation before writing the plot.

## 3. Shape

Shape the film from what the viewer should go through, not from a named structure. Writing into a template's slots gives every part the same weight, and the film marches from one section to the next.

- **Name the change:** what the viewer believes or feels at the start, and at the end. Material that neither sets it up nor delivers it is cut.
- **Open on a human truth** the audience recognises.
- **Turn on a change of view.** Show what the audience has always believed or could never see, then show it differently.
- **Find the few moments that carry it.** They get the time. The material between them moves quickly and is implied.
- **Decide for each thing the film conveys whether to imply it, explain it or show it off.**
  - **Imply** what the audience already knows: everyday actions, simple mechanics, well-known problems. Show a consequence and let the viewer complete it; no caption or reading confirms it. Something the viewer could not notice in the time it has on screen is implied this way or cut, not labelled.
  - **Explain in the scene** what is abstract or technical and has no picture of its own, so the viewer sees how it works in practice.
  - **Show off** machinery that is good to watch. Go close and keep it moving; what it does stays implied.

  Explained and shown-off things are the real interface or mechanism, not an abstract effect. Text never restates the picture.
- **Weight parallel material unevenly.** Tell one or two products, sites or features in depth and let the rest pass quickly. One unit repeated for each reads as a list.
- **Vary how each passage is told,** in pace, in what carries it and in whether it uses text.
- **Don't pay off every setup, or in order.** If each scene can be predicted from the one before, the film has become a checklist.
- **Raise something in every passage.** Two passages that could swap places without loss are one too many.
- **Let the opening and closing images answer each other,** and carry a recurring gesture or motif through the film so cuts can ride on it. The motif stays in what the viewer sees; neither narration nor text names it.

A named structure can check a finished draft, but not plan it.

## 4. Plot

Write one paragraph that tells the whole film. Then list its passages in order with their durations, mark the moments that carry it, and say for each whether it explains or shows off, and what; everything else is implied.

Scene rules:

- Every scene changes something the viewer can see or know. If nothing changes between its first and last frame, cut it or fold its information into another scene.
- Enter late and leave early. Start a scene once its action is under way and cut before it fully settles, so the film keeps moving.
- Show through action. A character doing something with an object reads faster than narration explaining it.
- Every scene gives the viewer enough to read who is doing what and why. A scene whose meaning depends on context the film has not shown gets that context in the picture.
- Link neighbouring scenes through a shared element. That link is what a match cut or a transition rides on, so name it in the plot.

## 5. Shot split

Break each scene into shots:

- Generate as few shots as the film needs. One continuous shot carries a move rather than two.
- Each shot has one job in the story. Two shots doing the same job is one too many.
- Each shot has one main action, written as start state, action, end state. Include hands and held objects when they change: who holds what, and where it ends up.
- A shot's end state must be a believable start for the next shot. An object that changes hands or position does so on screen, not between shots.
- An action never happens twice across shots. A long action is split where a visible state finishes, and each part keeps its own job.
- Fix screen direction, positions, eyelines and exits for the scene before choosing shot sizes. Keep the camera on one side of the line of action unless a shot crosses it on screen.
- Fix the direction of movement across cuts too: which way the camera moves, things travel and things turn. A move that runs against the next shot's breaks the cut.
- Prefer clarity over decorative camera movement. Each move needs a reason.
- Give every beat the viewer must notice enough screen time to register, starting with the first seconds, before the eye has settled.
- Do not build a beat on a fan standing still. Video models keep fans turning whatever the prompt says. When a stop or start is essential, generate the opposite change and play it reversed, as an insert with nothing else moving in it.

## 6. Duration

Time each shot from its action and sound first. Then read the target model's durations with `libtv-local models "MODEL DISPLAY NAME" --schema --json`:

- Shorter than the minimum: generate at the minimum and trim in post, or let the shot hold its end state.
- Longer than the maximum: split at a visible state change as in step 5.
- Shots that post-production will trim or speed-ramp get extra length as handles.

The shot durations add up to the target duration. Held frames and post-only shots count.

## 7. Generation, post and references

For every shot, decide per element what the model generates and what post adds. The model can generate almost anything a reference shows and a prompt describes, including moving and changing text. Send an element to post when post gives tighter control or costs less, usually because it would take many generations to get exactly right:

- **Exact timing or values matter.** Post places them to the frame; a generation has to be redone until it happens to match.
- **The motion design is complex.** Each attempt costs a full generation, while post iterates at no cost and leaves the shot underneath untouched.
- **The element varies between deliverables.** One generated shot serves every version.
- **The join between shots is a cut or a simple transition.** Freeze frames, speed ramps, split screens, grade matching, narration and music go to post as well.

Everything else stays with the model, including text and logos that a reference shows clearly. Shots made entirely in post stay in the table, marked as post.

Then list the references each generated shot needs by the kinds in `AGENTS.md`: environment, character, object, state, keyframe. Use the same reference name everywhere it appears so the asset list can be built by collecting the column. Reuse the approved references and takes the client file lists, under their original names, before planning new ones. A keyframe needs a stated reason: the motion or scene the other references cannot describe.

## 8. Output

Write two files in the project's `01-director/`:

- `plot.md`: the brief as agreed, the change the film makes, the plot paragraph, and the passages with durations and how each carrying moment is treated.
- `director-script.md`: a short note on look (light, colour, texture, camera style, the direction things move and turn), then the shot table.

Shot table columns:

| Column | Content |
|---|---|
| Shot | Scene and shot number, such as 2-3 |
| Duration | Seconds on screen, and generation length if different |
| Beat | The plot passage it belongs to |
| Job | What this shot does for the story |
| Action | Start state → action → end state |
| Camera | Shot size, angle, lens, movement |
| Sound | In-scene sound; narration and music lines if post adds them |
| Join | How it meets the next shot: cut, match cut on the shared element, dissolve, wipe, dip to black |
| Post | What post adds to this shot, or "none"; "post only" for shots without generation |
| References | Named references by kind, keyframe reason if any |

## 9. Check before handing over

- Every moment that carries the film has its shots and enough time.
- No caption or graphic restates what the picture shows, and parallel material is not told in one repeated pattern.
- Durations add up to the target.
- Every shot's end state leads into the next shot's start state, every join names its shared element or transition, and movement keeps its direction across each cut.
- No two shots share a job or repeat an action.
- Every generated shot lists its references, and every keyframe has its reason.
- Shots joined by a transition, carrying an overlay, played reversed or getting a speed ramp have the matching requirement in Post, so the shot prompt can include it.
