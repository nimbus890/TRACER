# Web development workflow

This repository is set up so Tracer can be developed from ChatGPT on the web without editing `main` directly.

## Branches

- `main` — stable source of truth.
- `web-dev` — browser/agent development branch.

Work should normally happen on `web-dev` or on short-lived branches created from it, then move to `main` through a pull request.

## Automatic tests

Changes pushed to `web-dev` and pull requests targeting `main` or `web-dev` run the Windows test workflow.

Local equivalent:

```powershell
python -m pip install -r requirements.txt
$env:QT_QPA_PLATFORM="offscreen"
python -m unittest discover -s tests -p "test_*.py" -v
```

## Manual Windows build

In GitHub:

1. Open **Actions**.
2. Select **Build Tracer for Windows**.
3. Choose **Run workflow** and select the branch you want to build.
4. When it finishes, download the **Tracer-Windows** artifact.

The build workflow installs the locked dependencies, downloads the bundled Tiny Whisper and visual-index models, runs `build.py`, and uploads a ZIP containing the standalone Windows build.

## Local sync

Before working locally:

```powershell
git switch web-dev
git pull
```

After local edits:

```powershell
git add .
git commit -m "Describe the change"
git push
```

ChatGPT can then read the new commit, continue development, inspect test failures, and open a PR back to `main`.
