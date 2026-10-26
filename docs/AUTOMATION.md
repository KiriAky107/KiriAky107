# Profile image automation

Workflow: `.github/workflows/profile-refresh.yml`.

## Triggers

- Daily at **06:17 Asia/Shanghai** (UTC cron: `17 22 * * *`). GitHub may queue or delay scheduled runs; execution at the exact minute is not guaranteed.
- Manually through Actions → **Refresh profile visuals** → **Run workflow**, selecting `main`.
- Automatically when changes to the workflow, 3D palette, media or profile-content catalogs, cover images, technology icons, card builders, image validator, or `README.md` are pushed to `main`. Commits that only update generated images do not match these paths.

## Components

| Component | Pinned version | Purpose |
| --- | --- | --- |
| [GitHub Readme Stats Action](https://github.com/stats-organization/github-readme-stats-action) | v2.1.0; core 2.2.0 | Public statistics and repository language cards, each with light and dark variants |
| [Platane/snk](https://github.com/Platane/snk) | v3.5.0, SVG entry point | Contribution snake animations in light and dark variants |
| [GitHub Profile 3D Contrib](https://github.com/yoshi389111/github-profile-3d-contrib) | v0.9.3 | One 3D contribution SVG containing both light and dark palettes |
| [lowlighter/metrics](https://github.com/lowlighter/metrics) | v3.34.0 | One anime and visual novel SVG containing the original work names, local covers, and both light and dark palettes |
| `scripts/build_profile_cards.py` | Tracked in this repository | Four project cards with public repository metadata, plus a categorized technology card; all five SVGs contain light and dark palettes |

Every Action is pinned to a full commit SHA, with its version noted in the workflow. Dependabot checks for Action updates every Monday and opens pull requests; automatic merging is not configured. The statistics renderer's `core_version: 2.2.0` is maintained separately.

## Data and permissions

No additional secret, personal access token (PAT), or external service account is required. The workflow uses GitHub's automatically provided `GITHUB_TOKEN`. It displays public data and does not enable private statistics or extended review/discussion fields that require additional permissions. If the account publicly displays anonymous private contribution counts, the contribution charts may include those published counts; private code is not read.

The generation job has only `contents: read`, and checkout does not persist Git credentials. A separate publishing job receives `contents: write`. It checks out the run's source commit, downloads the current run's image artifact, commits only the thirteen files below, and uses a normal fast-forward push without overwriting branch history. If `main` advances during the run, the push is rejected so outdated inputs cannot replace newer work.

```text
profile/stats-light.svg
profile/stats-dark.svg
profile/top-langs-light.svg
profile/top-langs-dark.svg
profile/snake-light.svg
profile/snake-dark.svg
profile/media.svg
profile/project-notes-articles.svg
profile/project-cpp-acm-notes.svg
profile/project-modern-python-notes.svg
profile/project-opennexus.svg
profile/technologies.svg
profile-3d-contrib/profile-custom.svg
```

The statistics cards use `hide_rank`. Language charts reflect public repository contents and **do not measure personal proficiency**. Commit and contribution counts are not skill ratings either.

## Appearance

- Statistics cards, contribution snakes, and the 3D chart share a blue/violet palette. Light mode uses blue `#5368d6` and violet `#7c6bd6`; dark mode uses blue `#8ea8ff` and violet `#a78bfa`.
- Contribution levels progress from `#eef1f8` to `#6574db` in light mode and from `#161b22` to `#9a9cf6` in dark mode. Both contribution visualizations use the same five-level scales.
- Statistics and snake colors are configured in the workflow. The 3D palette is configured in `.github/profile-3d-settings.json`, following the official [green-dual.json](https://github.com/yoshi389111/github-profile-3d-contrib/blob/main/sample-settings/green-dual.json) structure. Keep `fileName` set to `profile-custom.svg`.
- The media card uses `prefers-color-scheme` to select its light or dark palette within one SVG. Its titles, character names, and ordering come from `.github/profile-media.json`; cover art and character illustrations are read from `assets/covers/`. Update these source files to change the displayed entries.
- Project and technology cards use the same blue/violet colors and `prefers-color-scheme` switching. Their curated English text and technology categories come from `.github/profile-content.json`; local technology icon paths and their source credits are stored in `assets/icons/`.
- The README embeds SVGs stored in this repository, so visiting the profile does not require a public statistics service to render new images.

## Project and technology card rendering

`scripts/build_profile_cards.py` uses Python's standard library to generate five native SVGs during the same workflow run as the other profile images. It reads the four selected repositories through GitHub's [Repository REST API](https://docs.github.com/en/rest/repos/repos#get-a-repository), using the workflow's existing `GITHUB_TOKEN`. Stars, forks, primary language and last-push date come from public repository metadata. The English display titles and descriptions remain curated in `.github/profile-content.json`, so Chinese repository descriptions do not replace the English profile copy. Repositories with no detected primary language use the configured `language_fallback` label.

Each project is a separate image wrapped in its own repository link in the README. This keeps all four repository destinations clickable when GitHub renders the SVGs as images. The C++ and Python notes also retain their separate **Read online** links.

The technology card preserves five groups: **Languages**, **Desktop & UI**, **Services & Data**, **AI Applications**, and **Development**. Its 24 entries are selected explicitly in the catalog; they are not inferred from starred topics or presented as proficiency scores. Brand icons are embedded from the local icon catalog, while general concepts such as Agent, RAG, Skill and Plugin use simple interface symbols. The generated SVGs require no external image or font downloads.

## Media card rendering

`scripts/build_media_preset.py` reads the media catalog and local covers, then writes a JSON [Metrics preset](https://github.com/lowlighter/metrics/blob/65836723097537a54cd8eb90f61839426b4266b6/source/app/metrics/presets.mjs) with the `v1` schema. The preset contains the card markup, embedded cover data, and theme CSS through the official `extras_js` and `extras_css` inputs.

The preparation step places this preset in `/metrics_renders/media-preset.json`. Metrics mounts that directory as `/renders` inside its container and reads it with `config_presets: /renders/media-preset.json`. Keeping the complete preset in a file avoids passing image data through Action outputs or environment variables.

Metrics runs with `token: NOT_NEEDED`, `base: ""`, `base_skip: yes`, and `output_action: none`; it renders the repository's curated catalog without an AniList account or additional secret. `config_base64: no` disables Metrics' own image fetching; the preset already contains the local covers as data URIs. The Action writes `/metrics_renders/media.svg`, which is copied to `profile/media.svg` before validation. Only generated images enter the publishing artifact; the temporary preset stays on the generation runner.

The classic template is rendered at 480 pixels wide, with eight pixels of extra height to avoid clipping. The preset controls the background and light/dark colors. The catalog supports `list` rows for favorite works, a two-column `compact` layout for Watching & Playing, and a two-column `characters` gallery with square frames. Character illustrations are selected from each work’s original illustrator, with artist-owned posts or official publications preferred as sources. They retain their full proportions with `object-fit: contain`; each card includes the artist’s name. Original artwork and artist links are recorded in the catalog and listed in `docs/MEDIA.md`. Titles and character names use their English release names where available, or established romanizations. Animations are disabled for the media card; the existing contribution snake animations keep their own settings.

## Failure handling

The statistics Action sets `fail_on_error: true`. Before uploading, `python3 scripts/check_profile.py --generated --readme` checks that all thirteen images exist and are not error SVGs. It verifies every media title, illustration or cover, artist credit, section layout, and the rendered media card's measured height. The new cards are checked against the content catalog for project identity, English text, public counts, dates, technology group order, labels and icon keys. Expected entry counts come from the catalogs. The README check also verifies local image references, each project's clickable repository wrapper, and the two online-reading links.

Metrics logs exceptions from `extras_js` without necessarily failing the Action, so this content validation is required. The project builder also fails when it cannot retrieve valid public repository metadata. The publishing job validates the generated images again after downloading. If generation or validation fails, no update is committed, and the remote profile keeps its last successful images.

Inspect the failed step in Actions and rerun the workflow after resolving the cause. If `main` receives another commit during publishing and the push is rejected, rerun the complete workflow; it never force pushes. After changing the renderer version, palette, or file names, inspect the actual generated images as well.
