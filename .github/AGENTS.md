# GitHub Actions Workflows

<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-26 | Updated: 2026-04-26 -->

## Purpose

This directory contains GitHub Actions workflows for automated building and releasing of the WorldQuant Miner application across multiple platforms (Windows, Linux, macOS).

## Key Files

| File | Purpose | Triggers |
|------|---------|----------|
| `workflows/release.yml` | Build and release executables for all platforms | Push tags `v*`, manual dispatch |

## Workflows

### release.yml

Builds platform-specific executables and creates a GitHub release with downloadable assets.

**Jobs:**

| Job | Platform | Output |
|-----|----------|--------|
| `build-windows` | windows-latest | `generation-two.exe` |
| `build-linux` | ubuntu-latest | `*.deb` package |
| `build-macos` | macos-latest | `*.dmg` installer |
| `create-release` | ubuntu-latest | GitHub Release with all artifacts |

**Requirements:**

- Python 3.11
- `operatorRAW.json` constants file in `generation_two/constants/` or `constants/`
- Dependencies from `generation_two/requirements.txt`

**Manual Trigger:**

```bash
gh workflow run release.yml -f version=1.0.0
```

**Tag-based Trigger:**

```bash
git tag v1.0.0
git push origin v1.0.0
```

## For AI Agents

- All builds run in parallel; `create-release` waits for all to complete
- Constants file (`operatorRAW.json`) must exist before build
- Build script is `generation_two/build.py` with flags `--exe`, `--deb`, `--dmg`
- Release uses `softprops/action-gh-release@v2` action
- Artifacts are uploaded to GitHub Releases, not stored in repo
