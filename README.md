# Video workspace

An [Agent Workspaces](https://github.com/Q3yp/agent-workspaces) workspace for AI-assisted video production: direction, reference assets, shot generation, editing, narration, and delivery.

The guidelines describe a particular production workflow. Adapt them to your tools and creative needs. This repository contains reusable instructions and the `seamstitch` helper, not film projects, generated assets, or client material.

## Use it

```sh
git clone https://github.com/Q3yp/video-workspace.git ~/Workspaces/video
```

With the Agent Workspaces Codex plugin installed, run this from your `agent-workspaces` checkout:

```sh
uv run --offline --script plugins/codex/scripts/workspaces.py add ~/Workspaces/video
```

Registration adds the folder to Codex's write roots for future workspace-write sessions. Start a new session after registration; the plugin hook must be trusted in `/hooks`. The workspace is named `video-production`. If that name is already registered, use the existing workspace or choose a different frontmatter name before registering this clone.

You can also start an agent directly in the cloned folder and have it read `AGENTS.md`. `CLAUDE.md` imports the same instructions.

## Guidelines

- [AGENTS.md](AGENTS.md): shared rules, references, production order, and project layout.
- [direction.md](direction.md): brief, research, plot, and director script.
- [assets.md](assets.md): image prompts, references, generation, and review.
- [shots.md](shots.md): video prompts, takes, and review.
- [post.md](post.md): editing, graphics, narration, sound, and delivery.
- [genres.md](genres.md): brand-film and motion-graphics conventions.
- [models.md](models.md): provider-specific generation notes.

Create each film in its own subfolder using the layout in `AGENTS.md`. Keep client facts and approved assets in private project files. The root `.gitignore` allows only the shared guidance and tools into Git; newly created film folders remain ignored. Review files before changing that allowlist or force-adding anything.

## Tools and skills

These instructions assume an environment with a built-in image-generation tool, `libtv-local` for video/audio generation, and FFmpeg for media processing. Post-production may use Remotion or HyperFrames.

They also reference `asset-generation`, `conveying`, and `h3-prompt-writing` skills, and T3 delegation for the image-generating agent. Those integrations and skills are not bundled here. Install them separately if available, or adapt the corresponding guidelines to your environment. Follow the user's delegation authorization in `AGENTS.md`.

Provider names, model identifiers, and settings in `models.md` reflect the source workflow. Verify availability and current schemas in your own tools before generating. Model services may incur charges and require separate accounts. Keep credentials outside the repository.

## Optional seamstitch helper

[seamstitch](seamstitch/README.md) joins clips intended to appear continuous, with measured corrections near the cut. It requires Python, NumPy, Pillow, and `ffmpeg`/`ffprobe` on PATH.

From this repository's root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m seamstitch /path/to/config.json --dry-run
```

See its README for rendering, verification, and the local interface. Use trusted local files and a new output filename; the helper is a local utility, not a hosted service. It is published from the existing workflow without a new render-quality evaluation.

## License

Documentation and workspace instructions are licensed under [CC BY 4.0](LICENSE-CC-BY-4.0). Python code, configuration, and fenced code examples are licensed under [Apache 2.0](LICENSE-APACHE-2.0). Third-party tools, models, and media retain their own terms.
