---
trigger: model_decision
description: When the user asks to "release", "publish", or "push a new version", follow this process.
---
# Release Process Workflow

When the user asks to "release", "publish", or "push a new version", follow this process.

## Quick Alpha Release (Develop Branch)

Use for frequent alpha releases to testers:

```bash
# 1. Ensure all Python changes are formatted
python -m black app/

# 2. Run flake8 linting checks
python -m flake8 app/ --count --show-source --statistics
# Must show "0" errors before proceeding

# 3. Stage and commit any outstanding changes
git add -A
git commit -m 'Brief description of changes'

# 4. Run quick release script
python scripts/quick_release.py patch -m 'Description of changes'