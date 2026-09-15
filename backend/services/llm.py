import json
import os
from typing import Any, Dict

from groq import Groq


MODEL = "openai/gpt-oss-120b"


SYSTEM_PROMPT = """
You are the intent router for UPI Sentinel, an AI-powered UPI fraud and merchant
intelligence platform.

Your job is to understand a user's natural-language analytics question and map it
to exactly ONE supported intent.

Supported intents:

1. merchant_chargeback_ratio
   Questions about merchant categories, chargebacks, chargeback-to-transaction
   ratios, or which category has the highest chargeback ratio.

2. highest_risk_users
   Questions asking for highest-risk users, risky users, suspicious users, or
   user risk rankings.

3. suspicious_networks
   Questions about suspicious fraud networks, network chargeback rates,
   suspicious network components, or risky transaction networks.

4. investigation_queue
   Questions asking what should be investigated, investigation candidates,
   priority cases, or the investigation queue.

If the question does not clearly match one of these, use investigation_queue.

Choose an appropriate chart:
- merchant_chargeback_ratio -> bar
- highest_risk_users -> bar
- suspicious_networks -> bar
- investigation_queue -> bar

Return ONLY valid JSON in this exact shape:

{
  "intent": "one_supported_intent",
  "chart_type": "bar",
  "title": "short chart title",
  "time_scope": "all_data or latest_quarter"
}
"""


def _client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    return Groq(api_key=api_key)


def interpret_query(question: str) -> Dict[str, Any]:
    """
    Convert a natural-language question into a small structured intent.
    The LLM does not see the dataset and does not calculate statistics.
    """

    client = _client()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=300,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Groq returned an empty response")

    result = json.loads(content)

    allowed_intents = {
        "merchant_chargeback_ratio",
        "highest_risk_users",
        "suspicious_networks",
        "investigation_queue",
    }

    intent = result.get("intent", "investigation_queue")

    if intent not in allowed_intents:
        intent = "investigation_queue"

    chart_type = result.get("chart_type", "bar")

    if chart_type != "bar":
        chart_type = "bar"

    return {
        "intent": intent,
        "chart_type": chart_type,
        "title": result.get("title", "UPI Sentinel Analysis"),
        "time_scope": result.get("time_scope", "all_data"),
    }


def explain_result(question: str, analysis: Dict[str, Any]) -> str:
    """
    Generate a concise natural-language explanation from already-computed
    deterministic analytics results.
    """

    client = _client()

    prompt = f"""
You are the AI Investigator for UPI Sentinel.

The Python analytics engine has already calculated the following result.
Treat these numbers as authoritative. Do not invent or modify numbers.

User question:
{question}

Computed analysis:
{json.dumps(analysis, ensure_ascii=False)}

Write a concise investigator-style explanation in 2-4 sentences.

Mention:
- the main finding
- the most important number
- why it may matter for investigation

Do not claim that suspicious activity is proven fraud.
Use language such as "candidate", "signal", "flag", or "requires investigation"
where appropriate.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise financial fraud intelligence analyst.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_completion_tokens=250,
    )

    content = response.choices[0].message.content

    if not content:
        return "Analysis completed. Review the ranked results and investigate the highest-priority candidates."

    return content.strip()
