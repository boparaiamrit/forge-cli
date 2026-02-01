# Forge CLI - Gemini Guidelines

## Semantic Versioning Rules

When making changes to Forge CLI, follow these versioning guidelines:

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR** (X.0.0): Breaking changes that are not backwards compatible
  - Removing features or commands
  - Changing CLI argument structure
  - Major architecture changes
  - Python version requirement changes

- **MINOR** (0.X.0): New features that are backwards compatible
  - Adding new modules (e.g., disk/, alerts/, cve/)
  - Adding new menu options
  - New commands or subcommands
  - Significant enhancements to existing features

- **PATCH** (0.0.X): Bug fixes and minor improvements
  - Bug fixes
  - Documentation updates
  - Code refactoring without behavior changes
  - Minor UI improvements
  - Dependency updates

### When to Update Version

1. **Always update version when:**
   - Adding a new module
   - Adding significant new functionality
   - Fixing important bugs
   - Making any user-facing changes

2. **Files to update:**
   - `pyproject.toml` - Update `version = "X.X.X"`
   - `updater/__init__.py` - Update `CURRENT_VERSION = "X.X.X"`
   - `CHANGELOG.md` - Add entry at top with date and changes

### CHANGELOG Format

```markdown
## [X.X.X] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Changed feature description

### Fixed
- Bug fix description

### Removed
- Removed feature description
```

### Examples

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| New module added | MINOR | 0.9.0 → 0.10.0 |
| New menu option | MINOR | 0.9.0 → 0.10.0 |
| Bug fix | PATCH | 0.9.0 → 0.9.1 |
| Documentation update | PATCH | 0.9.0 → 0.9.1 |
| Breaking CLI change | MAJOR | 0.9.0 → 1.0.0 |
| Multiple minor features | MINOR | 0.9.0 → 0.10.0 |

### Before Committing

1. Update version in `pyproject.toml`
2. Update version in `updater/__init__.py`
3. Add CHANGELOG entry
4. Run tests: `docker build -t forge-cli-test . && docker run --rm forge-cli-test`
5. Commit with message: `vX.X.X: Brief description`

## PowerShell Command Guidelines

When running commands on Windows PowerShell, follow these rules:

### DO NOT
- Use long commit messages with multiple lines (use short single-line messages)
- Chain multiple Python imports with semicolons in one command
- Use complex shell commands with special characters
- Use multi-line strings in command arguments

### DO
- Keep commit messages short: `git commit -m "v0.10.0: Brief description"`
- Create temporary test scripts instead of inline Python code
- Use simple, single-purpose commands
- Break complex operations into multiple steps

### Examples

**BAD (too long, will fail):**
```powershell
git commit -m "v0.10.0: Feature 1
- Detail 1
- Detail 2"
```

**GOOD (short message):**
```powershell
git commit -m "v0.10.0: Add feature X"
```

**BAD (inline Python with semicolons):**
```powershell
python -c "import foo; import bar; print('ok')"
```

**GOOD (use test file or separate command):**
```powershell
docker run --rm forge-cli-test pytest tests/ -v
```

