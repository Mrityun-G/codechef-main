# CodeChef Practice Auto-Grinder

A GitHub Actions practice assistant that finds CodeChef Practice Archive problems, asks Gemini for a C++17-compatible or Python 3 solution, submits it when enabled, and records accepted solution IDs.

Generated answers are not guaranteed to be correct or original. This tool is for practice problems only; do not use it in contests or present its results as problems you solved yourself. The previous “0% MOSS / plagiarism risk” claim was removed because no tool can guarantee that.

## What it does

- Runs twice daily at 04:00 and 16:00 UTC, with a default target of five problems per run.
- Starts near rating 200 and raises the target band by 100 after every 20 tracked accepted problems, up to rating 1400.
- Reads problem statements and samples from CodeChef’s public practice endpoints.
- Extracts the current CSRF token from the problem page before submitting.
- Retries wrong answers, time limits, runtime errors, and compilation errors up to three times.
- Stores accepted CodeChef solution IDs and rechecks submissions that remain pending.
- Defaults to draft-only mode for local runs. A manual GitHub Actions run also defaults to draft-only mode.

The CodeChef endpoints used here are part of its website and can change without notice. CodeChef currently exposes `CPP20` and `PYTH 3` for practice; generated C++ is requested to stay compatible with C++17.

## Set up GitHub

1. Push this project to your repository. Check the repository URL in GitHub’s **Code** menu. This checkout’s remote was a placeholder; the URL inferred from the screenshot returned “Repository not found” when checked, so verify the owner, repository name, and access before pushing.
2. Under **Settings → Secrets and variables → Actions**, add secrets:
   - `GEMINI_API_KEY`: your Google AI Studio key.
   - `CODECHEF_SESSION`: the complete cookie pair, including its name, in the form `SESS...=value`.
3. Add repository variables:
   - `CODECHEF_USERNAME`: the CodeChef account that owns the session.
   - `GEMINI_MODELS` (optional): comma-separated model IDs for fallback, such as `gemini-3.8-flash`.
4. Under **Settings → Actions → General → Workflow permissions**, select **Read and write permissions**.
5. Open **Actions**, select **CodeChef Practice Auto-Grinder**, and click **Enable workflow** if GitHub shows it as disabled.
6. Use **Run workflow**. The `dry_run` input is enabled by default. Turn it off only when you want submissions sent to CodeChef.

Never put the CodeChef cookie or Gemini key in source files, workflow YAML, or commits. Session cookies expire; replace the secret if CodeChef logs the account out.

## Run locally

In PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY = "your-gemini-key"
$env:CODECHEF_USERNAME = "your-codechef-handle"
$env:DRY_RUN = "true"
python -m src.runner
```

Drafts are written under `drafts/` and are ignored by Git. To submit from a local run, set `CODECHEF_SESSION` to the full cookie pair and `DRY_RUN` to `false`.

## Existing solves

The tracker starts empty and only knows about accepted submissions recorded by this bot. Before enabling submissions, add known solved problem codes to the `solved` object in `data/solved_problems.json` so the runner skips them. The tracker is account-bound; changing `CODECHEF_USERNAME` archives the old file under `data/archive/` and starts a new one.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DAILY_TARGET` | `5` | Problems per run, from 1 to 8 |
| `MIN_RATING` | `200` | Starting difficulty |
| `MAX_RATING` | `1400` | Highest difficulty |
| `RATING_STEP` | `100` | Difficulty increase after 20 accepted problems |
| `MAX_ATTEMPTS` | `3` | Submissions per problem |
| `SOLUTION_LANGUAGE` | `cpp` | `cpp` or `python` |
| `DRY_RUN` | `true` | Generate drafts without submitting |

The GitHub schedule runs twice per day, so its default target can submit up to ten accepted practice solutions per day. Actual results depend on the model, the available problem ratings, account state, and CodeChef’s verdict timing.
