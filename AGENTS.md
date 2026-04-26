<!-- Generated: 2026-04-26 | Updated: 2026-04-26 -->

# worldquant-miner

## Purpose
Monorepo for WorldQuant alpha mining, prediction market research, and trading platforms. Contains multiple independent subprojects with different tech stacks and purposes. No global install command - choose subproject based on goal.

## Key Files
| File | Description |
|------|-------------|
| `CODEBASE_OVERVIEW.md` | Comprehensive guide to all subprojects and entry points |
| `README.md` | Repository overview |
| `credential.example.txt` | Template for WorldQuant Brain credentials |
| `.gitignore` | Git ignore patterns |
| `create_release.sh` | Release automation script |
| `create_release.ps1` | Windows release automation |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `generation_two/` | Main Python GUI alpha mining system (recommended entry) |
| `generation_one/` | Legacy and experimental implementations including naive-ollama, agent platforms |
| `polymarket/` | Python prediction-market research and execution framework |
| `tradr-platform/` | Next.js + NestJS trading game platform |
| `stone_age/` | Historical Python/Rust implementations |
| `mini-quant/` | Minimal quant experiments |
| `paper/` | English documentation/papers |
| `paper-zh/` | Chinese documentation/papers |
| `.github/` | GitHub Actions workflows |

## For AI Agents

### Working In This Directory
- This is a monorepo with independent subprojects
- No global package.json or requirements.txt
- Choose subproject based on user's goal before making changes
- Read `CODEBASE_OVERVIEW.md` for detailed entry point guidance

### Recommended Entry Points
| Goal | Directory |
|------|-----------|
| WorldQuant alpha mining with GUI | `generation_two/` |
| Docker + Ollama automation | `generation_one/naive-ollama/` |
| Prediction market research | `polymarket/` |
| Trading game platform | `tradr-platform/` |

### Testing Requirements
- Each subproject has its own test setup
- No repository-wide tests

### Common Patterns
- Credentials stored in `credential.txt` (JSON array format)
- Python projects use venv in `.venv/`
- TypeScript projects have separate `package.json` per subproject

## Dependencies

### External
- Python 3.10+ for Python subprojects
- Node.js 18+ for TypeScript subprojects
- Docker Desktop for containerized workflows
- Optional: NVIDIA GPU + NVIDIA Container Toolkit

<!-- MANUAL: Custom project notes can be added below -->
