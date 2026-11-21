import html
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
import requests

from src.config import config

logger = logging.getLogger("CodeChefClient")


class CodeChefAuthError(RuntimeError):
    """The CodeChef session cookie is missing, expired, or rejected.

    This is an infrastructure problem, not a property of the problem being
    solved, so callers must abort the run instead of blacklisting problems.
    """


class CodeChefAccountMismatch(RuntimeError):
    """The valid CodeChef session belongs to a different configured account."""


class SubmissionHistoryError(RuntimeError):
    """Submission history could not be verified safely."""


class VerdictTimeout(TimeoutError):
    """Judging did not finish in time. The submission may still be accepted."""

    def __init__(self, solution_id: str, waited: int):
        super().__init__(f"Submission {solution_id} timed out after {waited}s")
        self.solution_id = solution_id


class SubmissionsDisabled(RuntimeError):
    """CodeChef has temporarily disabled submissions for this one problem."""


_AUTH_HINTS = ("login", "log in", "logged in", "sign in", "unauthori", "session expired")


class CodeChefClient:
    BASE_URL = "https://www.codechef.com"
    API_LIST_PROBLEMS = f"{BASE_URL}/api/list/problems"
    API_PROBLEM_DETAILS = f"{BASE_URL}/api/contests/PRACTICE/problems"
    API_SUBMIT = f"{BASE_URL}/api/ide/submit"

    # Language mapping for CodeChef IDE
    LANG_MAP = {
        "cpp": "42",        # C++ (gcc 9.2.1)
        "c++": "42",
        "cpp17": "42",
        "python3": "116",   # Python 3.8
        "py": "116",
        "java": "10",       # Java
    }

    def __init__(self, session_cookie: str = ""):
        raw_session = session_cookie or config.codechef_session
        self.session_cookie = raw_session.strip().strip('"').strip("'") if raw_session else ""
        self.http = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.BASE_URL,
            "Origin": self.BASE_URL,
            "Connection": "keep-alive",
        }
        if self.session_cookie:
            if "=" not in self.session_cookie:
                raise ValueError("CODECHEF_SESSION must include the full cookie name=value pair.")
            cookie_name, cookie_value = self.session_cookie.split("=", 1)
            if not cookie_name.startswith("SESS") or not cookie_value:
                raise ValueError("CODECHEF_SESSION must have the form SESS...=value.")
            headers["Cookie"] = f"{cookie_name}={cookie_value}"

        self.http.headers.update(headers)

    def verify_authenticated_user(self, expected_username: str) -> str:
        """Verify that CodeChef accepts the session and reports the expected handle."""
        if not self.session_cookie:
            raise CodeChefAuthError("CODECHEF_SESSION is missing.")

        try:
            response = self.http.get(f"{self.BASE_URL}/api/user/me", timeout=15)
        except requests.RequestException as exc:
            raise CodeChefAuthError("Could not verify the CodeChef session due to a network error.") from exc

        if response.status_code in (401, 403):
            raise CodeChefAuthError(f"CodeChef rejected the session [HTTP {response.status_code}].")
        if response.status_code != 200:
            raise CodeChefAuthError(f"Could not verify the CodeChef session [HTTP {response.status_code}].")

        try:
            payload = response.json()
        except ValueError as exc:
            raise CodeChefAuthError("CodeChef returned an unreadable authentication response.") from exc

        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise CodeChefAuthError("CodeChef did not confirm an authenticated session.")
        user = payload.get("user") if isinstance(payload, dict) else None
        actual_username = user.get("username") if isinstance(user, dict) else None
        if not isinstance(actual_username, str) or not actual_username.strip():
            raise CodeChefAuthError("CodeChef did not identify an authenticated user for this session.")

        actual_username = actual_username.strip()
        if actual_username.casefold() != expected_username.strip().casefold():
            raise CodeChefAccountMismatch(
                f"Configured account '{expected_username}' does not match the authenticated CodeChef account."
            )
        return actual_username

    def has_prior_submission(self, problem_code: str) -> bool:
        """Return whether this account has ever submitted this Practice problem.

        Any prior attempt, regardless of verdict, is skipped to avoid accidental
        duplicate submissions. Unexpected or unavailable responses fail closed.
        """
        url = f"{self.BASE_URL}/api/problems/my-submissions/PRACTICE/{problem_code}"
        try:
            response = self.http.get(url, timeout=15)
        except requests.RequestException as exc:
            raise SubmissionHistoryError(
                f"Could not verify submission history for {problem_code} due to a network error."
            ) from exc

        if response.status_code in (401, 403):
            raise CodeChefAuthError(
                f"CodeChef rejected the session while checking submission history [HTTP {response.status_code}]."
            )
        if response.status_code != 200:
            raise SubmissionHistoryError(
                f"Could not verify submission history for {problem_code} [HTTP {response.status_code}]."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise SubmissionHistoryError(
                f"CodeChef returned unreadable submission history for {problem_code}."
            ) from exc

        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise SubmissionHistoryError(
                f"CodeChef did not confirm submission history for {problem_code}."
            )

        # CodeChef currently returns ``submissions`` at the top level; accept
        # the wrapped ``data.submissions`` form as well for API variants.
        submissions = payload.get("submissions")
        if not isinstance(submissions, list):
            data = payload.get("data")
            submissions = data.get("submissions") if isinstance(data, dict) else None
        if not isinstance(submissions, list):
            raise SubmissionHistoryError(
                f"CodeChef returned an unexpected submission history format for {problem_code}."
            )
        return bool(submissions)

    def fetch_practice_problems(
        self,
        page: int = 0,
        limit: int = 25,
        sort_by: str = "successful_submissions",
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """Fetch popular / graded practice problems from CodeChef."""
        params = {
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        response = self.http.get(self.API_LIST_PROBLEMS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    def fetch_problem_details(self, problem_code: str) -> Dict[str, Any]:
        """Fetch full description, constraints, and sample inputs for a problem."""
        url = f"{self.API_PROBLEM_DETAILS}/{problem_code}"
        response = self.http.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "success":
            raise ValueError(f"Could not retrieve details for {problem_code}: {data}")

        # Check if modern structured problemComponents exist
        comps = data.get("problemComponents")
        if comps and isinstance(comps, dict) and comps.get("statement"):
            parts = []
            if comps.get("statement"):
                parts.append(f"### Problem Statement:\n{self._clean_html(comps['statement'])}")
            if comps.get("inputFormat"):
                parts.append(f"### Input Format:\n{self._clean_html(comps['inputFormat'])}")
            if comps.get("outputFormat"):
                parts.append(f"### Output Format:\n{self._clean_html(comps['outputFormat'])}")
            if comps.get("constraints"):
                parts.append(f"### Constraints:\n{self._clean_html(comps['constraints'])}")
            if comps.get("sampleTestCases"):
                parts.append("### Sample Test Cases:")
                for stc in comps["sampleTestCases"]:
                    inp = stc.get("input", "").strip()
                    outp = stc.get("output", "").strip()
                    expl = stc.get("explanation", "").strip()
                    parts.append(f"Input:\n```\n{inp}\n```\nOutput:\n```\n{outp}\n```\nExplanation: {expl}")
            clean_content = "\n\n".join(parts)
        else:
            raw_body = data.get("body", "")
            raw_body = re.sub(
                r"^This is an example statement in markdown\..*?email us at help@codechef\.com\.\s*",
                "",
                raw_body,
                flags=re.DOTALL | re.IGNORECASE
            )
            clean_content = self._clean_html(raw_body)

        data["cleanContent"] = clean_content
        return data

    def get_csrf_token(self, problem_code: str) -> str:
        """Extract the dynamic window.csrfToken from CodeChef problem page."""
        url = f"{self.BASE_URL}/problems/{problem_code}"
        response = self.http.get(url, timeout=15)
        response.raise_for_status()

        match = re.search(r'window\.csrfToken\s*=\s*"([a-f0-9]+)"', response.text)
        if match:
            return match.group(1)
        raise ValueError(f"Could not find window.csrfToken on problem page {url}")

    def submit_solution(
        self,
        problem_code: str,
        code: str,
        language: str = "cpp",
    ) -> str:
        """Submit code to CodeChef IDE and return solution_id (upid)."""
        if not self.session_cookie:
            raise PermissionError("CODECHEF_SESSION is required to submit code to CodeChef.")

        csrf_token = self.get_csrf_token(problem_code)
        lang_id = self.LANG_MAP.get(language.lower(), "42")

        headers = {
            "Referer": f"{self.BASE_URL}/problems/{problem_code}",
            "x-csrf-token": csrf_token,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        payload = {
            "sourceCode": code,
            "language": lang_id,
            "problemCode": problem_code,
            "contestCode": "PRACTICE",
        }

        response = self.http.post(self.API_SUBMIT, data=payload, headers=headers, timeout=20)
        if response.status_code in (401, 403):
            # e.g. 403 {"status":"error","message":"Submissions on this problem are temporarily disabled"}
            response_hint = response.text[:300].lower()
            if "disabled" in response_hint and "problem" in response_hint:
                raise SubmissionsDisabled(f"Submissions are temporarily disabled for {problem_code}.")
            raise CodeChefAuthError(
                f"CodeChef rejected the session [HTTP {response.status_code}]."
            )
        if response.status_code != 200:
            raise RuntimeError(f"Submission failed [HTTP {response.status_code}].")

        try:
            res_data = response.json()
        except ValueError:
            raise RuntimeError("CodeChef returned a non-JSON submission response.")

        solution_id = str(res_data.get("upid") or res_data.get("solution_id") or "")
        if not solution_id:
            if any(h in json.dumps(res_data).lower() for h in _AUTH_HINTS):
                raise CodeChefAuthError("CodeChef reports that the session is not authenticated.")
            raise RuntimeError("CodeChef submission response did not include a solution id.")

        return solution_id

    def check_verdict_once(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the verdict for a submission once. Returns None while still judging."""
        url = f"{self.API_SUBMIT}?solution_id={solution_id}"
        try:
            response = self.http.get(url, timeout=15)
        except requests.RequestException as e:
            logger.warning(f"Verdict request for {solution_id} failed: {e}")
            return None
        if response.status_code in (401, 403):
            raise CodeChefAuthError(f"CodeChef rejected the session while polling [HTTP {response.status_code}]")
        if response.status_code != 200:
            return None
        try:
            data = response.json()
        except ValueError:
            return None
        result_code = str(data.get("result_code") or "").lower()
        # When evaluation finishes, result_code is not 'wait' / 'running' / empty
        if result_code and result_code not in ("wait", "running", "waiting", "compiling", "queued"):
            return self.parse_verdict(data)
        return None

    def poll_verdict(self, solution_id: str, max_wait_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Poll CodeChef IDE submit status until judging completes.

        Raises VerdictTimeout if judging does not finish in time. A timeout is
        NOT a rejection: the submission may still be accepted later.
        """
        wait = max_wait_seconds if max_wait_seconds is not None else config.verdict_timeout_seconds
        start_time = time.time()
        while True:
            verdict = self.check_verdict_once(solution_id)
            if verdict is not None:
                return verdict
            if time.time() - start_time >= wait:
                break
            time.sleep(2.5)
        raise VerdictTimeout(solution_id, wait)

    def fetch_profile_solved_count(self, username: str) -> Optional[int]:
        """Best-effort read of 'Total Problems Solved' from a public profile page.

        Used only for a warning-level consistency check; returns None if the
        page layout is not recognised.
        """
        try:
            response = self.http.get(f"{self.BASE_URL}/users/{username}", timeout=15)
            if response.status_code != 200:
                return None
            match = re.search(r"Total\s+Problems\s+Solved\s*:?\s*(?:<[^>]*>\s*)*(\d+)", response.text, re.I)
            return int(match.group(1)) if match else None
        except Exception as e:
            logger.info(f"Could not read profile solved count for {username}: {e}")
            return None

    def parse_verdict(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize CodeChef judging result into a structured feedback object."""
        result_code = str(raw_result.get("result_code", "unknown")).lower()
        status = str(raw_result.get("status", "")).lower()
        score = raw_result.get("score")
        
        # 'accepted' or 'correct' or 100 score means Accepted / AC on CodeChef
        passed = (
            result_code in ("correct", "accepted", "ac")
            or status in ("correct", "accepted")
            or score == 100
        )

        time_taken = raw_result.get("time", "N/A")
        memory_taken = raw_result.get("memory", "N/A")

        diagnostic = ""
        if not passed:
            if result_code == "wrong":
                diagnostic = (
                    f"Verdict: WRONG ANSWER (WA)\n"
                    f"Score: {raw_result.get('score', 0)}\n"
                    f"Message: {raw_result.get('custom__message', 'Incorrect output on testcases.')}"
                )
            elif result_code == "time":
                diagnostic = (
                    f"Verdict: TIME LIMIT EXCEEDED (TLE)\n"
                    f"Time Taken: {time_taken}s\n"
                    f"Action: Algorithm time complexity too high. Optimize loops / use fast I/O."
                )
            elif result_code == "compilation_error":
                diagnostic = (
                    f"Verdict: COMPILATION ERROR\n"
                    f"Compiler Log:\n{raw_result.get('cmp_info', 'Compilation failed.')}"
                )
            elif result_code == "runtime":
                diagnostic = (
                    f"Verdict: RUNTIME ERROR (SIGSEGV / NZEC)\n"
                    f"Signal: {raw_result.get('signal', 'Non-zero exit code')}\n"
                    f"Memory Limit / Bounds Exception."
                )
            else:
                diagnostic = f"Verdict: {result_code}\nDetails: {json.dumps(raw_result, indent=2)}"

        return {
            "passed": passed,
            "result_code": result_code,
            "time": time_taken,
            "memory": memory_taken,
            "diagnostic": diagnostic,
            "raw": raw_result,
        }

    @staticmethod
    def _clean_html(raw_html: str) -> str:
        """Convert HTML problem body into clean, legible text."""
        if not raw_html:
            return ""
        text = html.unescape(raw_html)
        text = re.sub(r"<pre>(.*?)</pre>", r"\n```\n\1\n```\n", text, flags=re.DOTALL)
        text = re.sub(r"<code>(.*?)</code>", r"`\1`", text)
        text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text)
        text = re.sub(r"<em>(.*?)</em>", r"*\1*", text)
        text = re.sub(r"<li>(.*?)</li>", r"- \1\n", text)
        text = re.sub(r"<p>", r"\n", text)
        text = re.sub(r"<br\s*/?>", r"\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
