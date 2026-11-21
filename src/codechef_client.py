from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.codechef.com/"


@dataclass(frozen=True)
class Problem:
    code: str
    name: str
    rating: int
    statement: str
    input_format: str
    output_format: str
    constraints: str
    samples: tuple[dict[str, str], ...]


class CodeChefError(RuntimeError):
    pass


class CodeChefClient:
    def __init__(self, session_cookie: str = "") -> None:
        self.http = requests.Session()
        self.http.headers.update(
            {
                "User-Agent": "CodeChefPracticeAssistant/1.0",
                "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            }
        )
        if session_cookie:
            cookie = session_cookie.strip()
            if "=" not in cookie:
                raise ValueError("CODECHEF_SESSION must include the cookie name and value")
            name, value = cookie.split("=", 1)
            if not name.startswith("SESS") or not value:
                raise ValueError("CODECHEF_SESSION must have the form SESS...=value")
            self.http.cookies.set(name, value, domain=".codechef.com", path="/")

    def _json(self, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.http.get(urljoin(BASE_URL, path), timeout=30, **kwargs)
        response.raise_for_status()
        try:
            payload = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise CodeChefError(f"CodeChef returned non-JSON data for {path}") from error
        if not isinstance(payload, dict):
            raise CodeChefError(f"CodeChef returned an unexpected response for {path}")
        return payload

    def _csrf_token(self, problem_code: str) -> str:
        response = self.http.get(f"{BASE_URL}problems/{problem_code}", timeout=30)
        response.raise_for_status()
        patterns = (
            r"window\.csrfToken\s*=\s*['\"]([^'\"]+)['\"]",
            r"csrfToken\s*[:=]\s*['\"]([^'\"]+)['\"]",
        )
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return unescape(match.group(1))
        raise CodeChefError("Could not find window.csrfToken on the problem page")

    def problem(self, code: str) -> Problem:
        payload = self._json(f"api/contests/PRACTICE/problems/{code}")
        if payload.get("status") != "success":
            raise CodeChefError(str(payload.get("message") or f"Could not load {code}"))
        components = payload.get("problemComponents") or {}
        soup = BeautifulSoup(payload.get("body") or "", "html.parser")
        samples = tuple(
            {
                "input": str(item.get("input") or ""),
                "output": str(item.get("output") or ""),
                "explanation": str(item.get("explanation") or ""),
            }
            for item in components.get("sampleTestCases", [])
            if not item.get("isDeleted")
        )
        return Problem(
            code=code,
            name=str(payload.get("problem_name") or code),
            rating=int(float(payload.get("difficulty_rating") or 0)),
            statement=soup.get_text("\n", strip=True),
            input_format=str(components.get("inputFormat") or ""),
            output_format=str(components.get("outputFormat") or ""),
            constraints=str(components.get("constraints") or ""),
            samples=samples,
        )

    def discover(self, min_rating: int, max_rating: int, excluded: set[str]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        limit = 100
        for page in range(100):
            payload = self._json(
                "api/list/problems",
                params={"limit": limit, "page": page},
            )
            rows = payload.get("data") or []
            if not isinstance(rows, list):
                raise CodeChefError("CodeChef problem-list response has no data array")
            for row in rows:
                try:
                    code = str(row["code"])
                    rating = int(float(row.get("difficulty_rating") or 0))
                except (KeyError, TypeError, ValueError):
                    continue
                if code not in excluded and min_rating <= rating <= max_rating:
                    candidates.append(
                        {"code": code, "name": str(row.get("name") or code), "rating": rating}
                    )
            if len(rows) < limit:
                break
        return candidates

    def language_id(self, problem_code: str, preferred: str) -> str:
        payload = self._json(f"api/ide/PRACTICE/languages/{problem_code}")
        accepted_names = {
            "cpp": {"CPP20", "CPP17", "C++"},
            "python": {"PYTH 3", "PYTHON3"},
        }
        for language in payload.get("languages") or []:
            qualified_name = str(language.get("short_qualified_name", "")).upper()
            short_name = str(language.get("short_name", "")).upper()
            if qualified_name in accepted_names[preferred] or short_name in accepted_names[preferred]:
                return str(language["id"])
        raise CodeChefError(f"CodeChef does not list a supported {preferred} language for {problem_code}")

    def submit(self, problem_code: str, language_id: str, source: str) -> str:
        csrf_token = self._csrf_token(problem_code)
        response = self.http.post(
            f"{BASE_URL}api/ide/submit",
            data={
                "sourceCode": source,
                "language": language_id,
                "problemCode": problem_code,
                "contestCode": "PRACTICE",
            },
            headers={
                "Referer": f"{BASE_URL}submit/{problem_code}",
                "X-CSRFToken": csrf_token,
                "X-CSRF-Token": csrf_token,
            },
            timeout=30,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise CodeChefError("CodeChef returned non-JSON data after submission") from error
        if payload.get("status") == "error":
            errors = payload.get("errors") or [payload.get("message") or "submission rejected"]
            raise CodeChefError(", ".join(map(str, errors)))
        solution_id = payload.get("solution_id") or payload.get("submission_id") or payload.get("id")
        if not solution_id and isinstance(payload.get("data"), dict):
            data = payload["data"]
            solution_id = data.get("solution_id") or data.get("submission_id") or data.get("id")
        if not solution_id:
            raise CodeChefError(f"Submission response did not include a solution ID: {payload}")
        return str(solution_id)

    def verdict(self, solution_id: str) -> str:
        payload = self._json("api/ide/submit", params={"solution_id": solution_id})
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        for key in ("result_code", "verdict", "status"):
            value = data.get(key)
            if isinstance(value, str):
                normalized = value.strip().lower().replace(" ", "_")
                if normalized not in {"success", "pending", "queued", "running"}:
                    return normalized
        return "pending"

    def wait_for_verdict(self, solution_id: str, timeout_seconds: int = 120) -> str | None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            result = self.verdict(solution_id)
            if result != "pending":
                return result
            time.sleep(4)
        return None


def is_accepted(verdict: str) -> bool:
    return verdict in {"ac", "accepted", "correct", "fully_correct"}


def is_retryable(verdict: str) -> bool:
    return verdict in {
        "wrong",
        "wrong_answer",
        "wa",
        "tle",
        "time_limit_exceeded",
        "runtime_error",
        "compilation_error",
        "ce",
    }
