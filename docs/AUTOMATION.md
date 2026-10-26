# Profile image automation

Workflow: `.github/workflows/profile-refresh.yml`.

## Triggers

- Daily at **06:17 Asia/Shanghai** (UTC cron: `17 22 * * *`). GitHub may queue or delay scheduled runs; execution at the exact minute is not guaranteed.
- Manually through Actions → **Refresh profile visuals** → **Run workflow**, selecting `main`.
- Automatically when changes to the workflow, 3D palette, image validator, or `README.md` are pushed to `main`. Commits that only update generated images do not match these paths.

## Components

| Component | Pinned version | Purpose |
| --- | --- | --- |
| [GitHub Readme Stats Action](https://github.com/stats-organization/github-readme-stats-action) | v2.1.0; core 2.2.0 | Public statistics and repository language cards, each with light and dark variants |
| [Platane/snk](https://github.com/Platane/snk) | v3.5.0, SVG entry point | Contribution snake animations in light and dark variants |
| [GitHub Profile 3D Contrib](https://github.com/yoshi389111/github-profile-3d-contrib) | v0.9.3 | One 3D contribution SVG containing both light and dark palettes |

Every Action is pinned to a full commit SHA, with its version noted in the workflow. Dependabot checks for Action updates every Monday and opens pull requests; automatic merging is not configured. The statistics renderer's `core_version: 2.2.0` is maintained separately.

## Data and permissions

No additional secret, personal access token (PAT), or external service account is required. The workflow uses GitHub's automatically provided `GITHUB_TOKEN`. It displays public data and does not enable private statistics or extended review/discussion fields that require additional permissions. If the account publicly displays anonymous private contribution counts, the contribution charts may include those published counts; private code is not read.

The generation job has only `contents: read`, and checkout does not persist Git credentials. A separate publishing job receives `contents: write`. It downloads the current run's image artifact, commits only the seven files below, and uses a normal fast-forward push without overwriting branch history.

```text
profile/stats-light.svg
profile/stats-dark.svg
profile/top-langs-light.svg
profile/top-langs-dark.svg
profile/snake-light.svg
profile/snake-dark.svg
profile-3d-contrib/profile-custom.svg
```

The statistics cards use `hide_rank`. Language charts reflect public repository contents and **do not measure personal proficiency**. Commit and contribution counts are not skill ratings either.

## Appearance

- Statistics cards, contribution snakes, and the 3D chart share a blue/violet palette. Light mode uses blue `#5368d6` and violet `#7c6bd6`; dark mode uses blue `#8ea8ff` and violet `#a78bfa`.
- Contribution levels progress from `#eef1f8` to `#6574db` in light mode and from `#161b22` to `#9a9cf6` in dark mode. Both contribution visualizations use the same five-level scales.
- Statistics and snake colors are configured in the workflow. The 3D palette is configured in `.github/profile-3d-settings.json`, following the official [green-dual.json](https://github.com/yoshi389111/github-profile-3d-contrib/blob/main/sample-settings/green-dual.json) structure. Keep `fileName` set to `profile-custom.svg`.
- The README embeds SVGs stored in this repository, so visiting the profile does not require a public statistics service to render new images.

## Failure handling

The statistics Action sets `fail_on_error: true`. Before uploading, `python3 scripts/check_profile.py --generated` checks that all seven images exist and are not error SVGs. The publishing job validates them again after downloading. If generation or validation fails, no update is committed, and the remote profile keeps its last successful images.

Inspect the failed step in Actions and rerun the workflow after resolving the cause. If `main` receives another commit during publishing and the push is rejected, rerun the complete workflow; it never force pushes. After changing the renderer version, palette, or file names, inspect the actual generated images as well.
