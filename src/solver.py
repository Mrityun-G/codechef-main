from __future__ import annotations

import re

from google import genai

from .codechef_client import Problem


class GeminiSolver:
    def __init__(self, api_key: str, model_names: tuple[str, ...]) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model_names = model_names

    def solve(
        self,
        problem: Problem,
        language: str,
        previous_source: str = "",
        previous_verdict: str = "",
    ) -> tuple[str, str]:
        language_name = "C++17-compatible code" if language == "cpp" else "Python 3 code"
        reflection = ""
        if previous_source:
            reflection = (
                f"\nYour previous attempt received {previous_verdict}. Diagnose the likely issue and "
                "produce a corrected complete solution.\nPrevious source:\n"
                f"{previous_source}\n"
            )
        prompt = f"""Solve this CodeChef practice problem.

Problem: {problem.name} ({problem.code})
Statement:
{problem.statement}

Input format:
{problem.input_format}

Output format:
{problem.output_format}

Constraints:
{problem.constraints}

Samples:
{problem.samples}
{reflection}
Return only a complete {language_name} source file. Do not use markdown fences or include an explanation.
"""
        errors: list[str] = []
        for model_name in self.model_names:
            try:
                result = self.client.interactions.create(model=model_name, input=prompt)
                source = self._extract_source(result.output_text or "")
                if source:
                    return source, model_name
                errors.append(f"{model_name}: empty response")
            except Exception as error:
                errors.append(f"{model_name}: {error}")
        raise RuntimeError("Gemini models failed: " + " | ".join(errors))

    @staticmethod
    def _extract_source(text: str) -> str:
        fenced = re.search(
            r"```(?:cpp|c\+\+|cc|python|py)?\s*\n(.*?)```",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        source = fenced.group(1) if fenced else text
        return source.strip() + "\n" if source.strip() else ""
