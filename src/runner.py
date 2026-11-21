from __future__ import annotations

from datetime import datetime, timezone
import json
import random
import re
from pathlib import Path
from typing import Any

from .codechef_client import CodeChefClient, Problem, is_accepted, is_retryable
from .config import Config
from .solver import GeminiSolver


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "solved_problems.json"


def _load_state(username: str) -> dict[str, Any]:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        return {"account": username, "solved": {}, "pending": [], "attempts": {}}
    state = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    previous_account = state.get("account")
    if previous_account and previous_account.casefold() != username.casefold():
        archive_dir = DATA_PATH.parent / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        account_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", str(previous_account))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_path = archive_dir / f"solved_problems-{account_slug}-{stamp}.json"
        archive_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"Archived state for previous account to {archive_path.relative_to(ROOT)}")
        return {"account": username, "solved": {}, "pending": [], "attempts": {}}
    state["account"] = username
    state.setdefault("solved", {})
    state.setdefault("pending", [])
    state.setdefault("attempts", {})
    return state


def _save_state(state: dict[str, Any]) -> None:
    temporary_path = DATA_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_path.replace(DATA_PATH)


def _solution_paths(problem_code: str, language: str, dry_run: bool) -> tuple[Path, Path]:
    folder = ROOT / ("drafts" if dry_run else "solutions") / problem_code
    extension = "cpp" if language == "cpp" else "py"
    source_name = f"candidate.{extension}" if dry_run else f"solution.{extension}"
    return folder / source_name, folder / "README.md"


def _write_solution(
    problem: Problem,
    source: str,
    model_name: str,
    language: str,
    dry_run: bool,
    solution_id: str | None = None,
) -> None:
    source_path, readme_path = _solution_paths(problem.code, language, dry_run)
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8")
    status = "Draft; not submitted" if dry_run else f"Accepted as solution `{solution_id}`"
    language_name = "C++17-compatible" if language == "cpp" else "Python 3"
    readme_path.write_text(
        f"# {problem.name} ({problem.code})\n\n"
        f"- Difficulty: {problem.rating}\n"
        f"- Language: {language_name}\n"
        f"- Model: {model_name}\n"
        f"- Status: {status}\n"
        f"- Problem: https://www.codechef.com/problems/{problem.code}\n",
        encoding="utf-8",
    )


def _rating_band(config: Config, solved_count: int) -> tuple[int, int]:
    base = min(config.max_rating, config.min_rating + (solved_count // 20) * config.rating_step)
    return base, min(config.max_rating, base + config.rating_step - 1)


def _refresh_pending(client: CodeChefClient, state: dict[str, Any]) -> None:
    still_pending = []
    for item in state.get("pending", []):
        try:
            verdict = client.verdict(str(item["solution_id"]))
        except Exception as error:
            print(f"Could not recheck {item.get('problem_code')}: {error}")
            still_pending.append(item)
            continue
        if is_accepted(verdict):
            code = str(item["problem_code"])
            state["attempts"].setdefault(code, {})["last_verdict"] = verdict
            state["solved"][code] = {
                "solution_id": str(item["solution_id"]),
                "rating": item.get("rating"),
                "accepted_at": datetime.now(timezone.utc).isoformat(),
            }
            problem = Problem(
                code=code,
                name=str(item.get("name") or code),
                rating=int(item.get("rating") or 0),
                statement="",
                input_format="",
                output_format="",
                constraints="",
                samples=(),
            )
            _write_solution(
                problem,
                str(item.get("source") or ""),
                str(item.get("model") or "unknown"),
                str(item.get("language") or "cpp"),
                False,
                str(item["solution_id"]),
            )
            print(f"Pending submission {code} is now accepted")
        elif is_retryable(verdict):
            record = state["attempts"].setdefault(str(item["problem_code"]), {})
            record["last_verdict"] = verdict
            record["last_source"] = item.get("source", "")
            print(f"Pending submission {item.get('problem_code')} finished with {verdict}")
        else:
            still_pending.append(item)
    state["pending"] = still_pending


def _solve_problem(
    config: Config,
    client: CodeChefClient,
    solver: GeminiSolver,
    problem: Problem,
    state: dict[str, Any],
) -> bool:
    attempt_record = state["attempts"].setdefault(problem.code, {})
    prior_source = str(attempt_record.get("last_source") or "")
    prior_verdict = str(attempt_record.get("last_verdict") or "")
    next_attempt = int(attempt_record.get("count", 0)) + 1
    for attempt in range(next_attempt, config.max_attempts + 1):
        source, model_name = solver.solve(problem, config.preferred_language, prior_source, prior_verdict)
        if config.dry_run:
            _write_solution(problem, source, model_name, config.preferred_language, True)
            print(f"Drafted {problem.code} (rating {problem.rating}) with {model_name}")
            return False
        language_id = client.language_id(problem.code, config.preferred_language)
        solution_id = client.submit(problem.code, language_id, source)
        attempt_record.update({"count": attempt, "last_source": source, "last_verdict": "pending"})
        verdict = client.wait_for_verdict(solution_id)
        if verdict is None:
            state.setdefault("pending", []).append(
                {
                    "problem_code": problem.code,
                    "name": problem.name,
                    "rating": problem.rating,
                    "solution_id": solution_id,
                    "source": source,
                    "model": model_name,
                    "language": config.preferred_language,
                    "attempt": attempt,
                }
            )
            print(f"{problem.code} is still pending as solution {solution_id}")
            return False
        print(f"{problem.code} attempt {attempt}: {verdict}")
        attempt_record["last_verdict"] = verdict
        if is_accepted(verdict):
            state["solved"][problem.code] = {
                "solution_id": solution_id,
                "rating": problem.rating,
                "accepted_at": datetime.now(timezone.utc).isoformat(),
            }
            _write_solution(
                problem,
                source,
                model_name,
                config.preferred_language,
                False,
                solution_id,
            )
            return True
        if not is_retryable(verdict):
            attempt_record["exhausted"] = True
            print(f"Stopping retries for {problem.code} after non-retryable verdict {verdict}")
            return False
        prior_source = source
        prior_verdict = verdict
    attempt_record["exhausted"] = True
    return False


def run() -> None:
    config = Config.from_env()
    client = CodeChefClient(config.codechef_session)
    solver = GeminiSolver(config.gemini_api_key, config.model_names)
    state = _load_state(config.codechef_username)
    _refresh_pending(client, state)
    _save_state(state)

    solved_count = len(state["solved"])
    low_rating, high_rating = _rating_band(config, solved_count)
    excluded = set(state["solved"])
    excluded.update(str(item.get("problem_code")) for item in state.get("pending", []))
    excluded.update(
        code
        for code, attempt in state["attempts"].items()
        if attempt.get("exhausted") or int(attempt.get("count", 0)) >= config.max_attempts
    )
    candidates = client.discover(low_rating, high_rating, excluded)
    if not candidates and high_rating < config.max_rating:
        high_rating = min(config.max_rating, high_rating + config.rating_step)
        candidates = client.discover(low_rating, high_rating, excluded)
    random.shuffle(candidates)
    print(
        f"Account={config.codechef_username}, dry_run={config.dry_run}, "
        f"target={config.daily_target}, rating={low_rating}-{high_rating}"
    )

    for selected in candidates[: config.daily_target]:
        code = selected["code"]
        try:
            problem = client.problem(code)
            _solve_problem(config, client, solver, problem, state)
        except Exception as error:
            print(f"Skipping {code} after error: {error}")
        finally:
            _save_state(state)

    _save_state(state)
    print(f"Accepted records tracked: {len(state['solved'])}; pending submissions: {len(state['pending'])}")


if __name__ == "__main__":
    run()
