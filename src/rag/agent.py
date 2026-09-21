"""LLM agent orchestrating pharmacovigilance tools via Claude tool use."""
import json

from anthropic import Anthropic

from src.config import ANTHROPIC_API_KEY
from src.rag.tools import TOOL_SCHEMAS
from src.rag.tool_impl import TOOL_DISPATCH


MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 2048
MAX_TURNS = 8  # Safety cap on tool-use iterations

SYSTEM_PROMPT = """You are an expert pharmacovigilance analyst assisting a
pharmacist with questions about GLP-1 receptor agonists (semaglutide,
liraglutide, tirzepatide, dulaglutide, exenatide, lixisenatide) using the
FDA Adverse Event Reporting System (FAERS) 2024 dataset.

CRITICAL rules for every answer:

- NEVER claim causation. Spontaneous reports show ASSOCIATION only.
- ALWAYS cite the number of reports supporting each statement (e.g. 'n=818').
- ALWAYS note limitations of spontaneous reporting: underreporting, notoriety
  bias, absence of a proper denominator, confounding by indication.
- If evidence is thin (< 3 co-occurring cases), state that explicitly.
- Distinguish statistical signal from clinical relevance.
- Present disproportionality results with the metric NAME (PRR, ROR, IC)
  so the user can interpret confidence.

Workflow:
- For lay-term events ('liver issues', 'vision problems'), FIRST call
  `semantic_event_search` to translate into MedDRA PTs.
- For open-ended safety questions on a drug, call `detect_signals`.
- For demographic subgroup questions, use `query_cohort_events`.
- For head-to-head comparisons, use `compare_drugs`.

Respond in the same language the user used. Keep answers concise, structured,
and grounded in the data returned by tools.
"""


client = Anthropic(api_key=ANTHROPIC_API_KEY)


def _run_tool(name: str, arguments: dict) -> str:
    """Execute a tool and return its result as a JSON string."""
    if name not in TOOL_DISPATCH:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = TOOL_DISPATCH[name](**arguments)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": name, "arguments": arguments})


def ask(question: str, verbose: bool = True) -> str:
    """Send a question to Claude and iterate through tool calls until final answer."""
    messages = [{"role": "user", "content": question}]

    for turn in range(MAX_TURNS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if verbose:
            print(f"\n--- Turn {turn + 1} | stop_reason={response.stop_reason} ---")

        # Collect tool uses (if any) and text
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        # Add assistant response to conversation history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn" or not tool_uses:
            # Return concatenated text
            return "\n".join(b.text for b in text_blocks)

        # Execute every tool call requested this turn
        tool_results = []
        for tu in tool_uses:
            if verbose:
                print(f"  [tool] {tu.name}({json.dumps(tu.input)[:120]})")
            output = _run_tool(tu.name, tu.input)
            if verbose:
                print(f"  [result] {output[:200]}...")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": output,
            })

        messages.append({"role": "user", "content": tool_results})

    return "[Agent stopped after max turns without a final answer.]"


if __name__ == "__main__":
    demo_questions = [
        "¿Qué señales de seguridad emergentes aparecen para semaglutida en 2024?",
        "¿Hay reportes de problemas hepáticos con tirzepatida?",
        "Comparame el perfil de pancreatitis entre semaglutida, liraglutida y tirzepatide.",
    ]
    for q in demo_questions:
        print(f"\n{'='*70}\nQ: {q}\n{'='*70}")
        answer = ask(q)
        print(f"\nA: {answer}\n")