# Assets

Steps 4 to 6 of the production order: turn the References column of the director script into approved images in `02-assets/`. The reference kinds and what a reference does to a shot are in `AGENTS.md`; the image model's own rules and how to reach the generating agent are in `models.md`.

## Asset list

Collect every reference named in the shot table, once each, with the shots that use it and the scale each shot needs. Mark the ones reused from the client's approved assets; everything else is generated.

## Prompt file

For more than one asset, write all the image prompts into one prompt file in `03-prompts/`, one file per round. For each asset the file gives the prompt in its final wording, the references to attach in order with their roles, whether it is a fresh generation or an edit and of which file, how many candidates to generate, and where to save them. A later round opens with what the previous round got wrong and what this one changes. One agent runs the whole file, because one model working from one file keeps the set consistent.

Attach existing files by path: the client's own images (product renders, drawings, frames of its footage, which a search cannot find), approved assets and real photographs already in the workspace.

When a layout, scene or mechanism needs a real photograph to come out realistic and the workspace has none, the file names what that photograph must show and its role, and the generating agent finds it. A written description of a physical arrangement does not fix it; a photograph of the arrangement does.

- **A client's render, drawing or product animation shows the product's identity and shape, not how it is installed.** Take mounting, height, tilt, spacing and placement from a real photograph of the product or its kind in use, and counts and proportions from the client's drawing.
- **A photograph passes its own subject's features into the result,** whatever role it is given. A photograph of another maker's product brings its colours, counts and details with it. Describe the visible features the client's product has, so the agent finds a photograph that shares them, and say what in it must not carry over.

## Image prompts

Every asset prompt, single or batch, follows these rules. Two failures matter most, because every shot generated from an asset inherits them: the glossy "AI look", and stiffness.

- **Start with the image you need:** its use in the film and its medium, a photorealistic photograph. The intended use sets how polished the model makes the image.
- **Write sentences under labelled sections:** intended use, scene, subject, camera, light and colour, in that order, each in full sentences as a photographer would describe the frame. Add a details or constraints section only for what the other sections leave out.
- **Describe a moment that is under way.** Say what each person or animal is doing, with what, where they look, and how much of the body is in frame. A character sheet keeps its plain backdrop but still says how the person stands.
- **People look like ordinary people of their time and place.** Keep neutral white balance.
- **Animals or objects in a group differ** in size, angle, posture and what each is doing at that moment. A group drawn alike reads as mutated. Take a behaviour such as animals crowding or surfacing from a real photograph of it.
- **Treat camera terms as cues for the look, and put the layout in words:** what sits where in the frame, how much of it it fills, which way it faces. When a shot depends on an exact layout or mechanism, name a real photograph of it as a reference.
- **Give each reference a number and one role,** and say how the references combine and what goes where. Real photographs serve as references for texture, light, layout and period. Approved generated assets serve as references for identity only, because a generated image used as a style reference passes its polish on to every image made from it.
- **For an edit, say what changes and list what stays,** and exclude added text or watermarks. A region that must stay pixel-identical is composited in post.
- **Quote exact text** with its position, typography and how many times it appears, and ask for no other text. Spell unusual names letter by letter.
- **Name the place and date for period subjects,** and ask for period-accurate clothing, props and environment.
- **Leave the film's look to the grade.** Warmth, contrast and grain are added in post, not in the asset prompts.

## Editing an image

An edit redraws the whole picture, not only the part it was asked to change, and every pass coarsens fine texture into a repeated speckle that every shot generated from the image inherits.

- **An image is edited once at most.** The edit target is a real photograph or a fresh generation, never the result of an earlier edit.
- **If the edit does not work, do not edit its result.** Generate the image afresh from the original references with a corrected prompt.
- **Images that must share one framing** start from one freshly generated base, and each of the others is a single edit of that base. They are never edited from one another.

## Generating a prompt file

When you were handed a prompt file to generate: find each real photograph the file names, save it in the project's `02-assets/sources-real/` and add its source and licence to `SOURCES.md` there. Generate each item yourself with your built-in image tool, using the prompt as written, the listed references and the listed number of candidates, and save each result at its path. Report the saved files, the photographs found and any generation that failed. Judging and repairing the images is the director's job.

## Review

Look at every image at full size beside its references before it is used for anything, and pick between candidates. Decide per asset what makes it unusable and what does not matter, so the review does not turn into a hunt for small differences:

- **Must hold**: the layout or mechanism the shot depends on, the identity cues a viewer would notice, texture that reads as a photograph, and anything the user has already corrected.
- **Has room**: whatever may differ from the references without a viewer noticing, and framing that a crop can fix.

An image that passes its must-hold list is accepted. For one that fails, write a corrected prompt or choose a better reference, and send it for a fresh generation in a new prompt file. A rejected file keeps a `rejected-` prefix, and a rejected real photograph keeps the reason in `SOURCES.md`, so neither is attached again. After two or three rounds on the same asset, stop and show the user what is still wrong.

An approved asset from an earlier film gets the same review before it is reused, because it may predate the current rules.

A real photograph appears in the film itself only when its licence allows it. Otherwise it guides generation and nothing more.
