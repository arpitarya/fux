"""Headless AI self-critique — the ONLY model-importing module, behind the `[critic]` extra.

Used only when no host session can self-critique (the deferred runtime critic, plan §5/§7d);
the default build-agent path uses the agent's own tokens via the `critic` skill. This module
is NOT on the maintenance/enforcement path — `fux check`/`gate`/`critic`/`criticloop` never
import it. The model client is imported LAZILY (inside `judge`) so `import fux.criticllm`
stays cheap and dependency-free until you opt in with `pip install fux-engine[critic]`.
"""
from __future__ import annotations

from fux.criticloop import Verdict
from fux.model import Rule

_PROMPT = ("Critique a proposed change against ONE principle, and only that principle.\n"
           "Principle: {principle}\n\nProposed change:\n{proposal}\n\n"
           "First line: 'pass' or 'fail'. Second line: one sentence of rationale.")


def judge(proposal: str, principle: Rule, model: str = "claude-opus-4-8") -> Verdict:
    """AI self-critique of `proposal` against one judgment principle → Verdict. Requires the
    `[critic]` extra; the import is lazy so the default install stays model-free ($0)."""
    try:
        import anthropic
    except ModuleNotFoundError as e:
        raise RuntimeError("fux: the AI critic needs `pip install fux-engine[critic]`") from e
    text = (anthropic.Anthropic().messages.create(
        model=model, max_tokens=200,
        messages=[{"role": "user", "content": _PROMPT.format(
            principle=principle.fm.get("principle", principle.id), proposal=proposal)}],
    ).content[0].text.strip())
    status = "fail" if text.lower().startswith("fail") else "pass"
    rationale = text.split("\n", 1)[1].strip() if "\n" in text else ""
    return Verdict(principle.id, status, rationale)
