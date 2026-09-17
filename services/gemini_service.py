import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


def analyze_request_with_gemini(message, allowed_issue_types):
    """
    Use Gemini to understand the employee request.

    Gemini is used for natural-language understanding only.
    Final policy decisions remain in the deterministic agent core.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {
            "success": False,
            "issue_type": None,
            "summary": "",
            "error": "GEMINI_API_KEY is not configured."
        }

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the natural-language understanding layer for an internal IT
service agent.

Analyze the employee request below.

Choose exactly one issue_type from this allowed list:
{json.dumps(allowed_issue_types)}

Return ONLY valid JSON in this format:

{{
  "issue_type": "one allowed value",
  "summary": "short factual summary of the employee's problem"
}}

Do not provide a solution.
Do not invent company policies.
Do not add fields.

Employee request:
{message}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        result = json.loads(response.text)

        if result.get("issue_type") not in allowed_issue_types:
            return {
                "success": False,
                "issue_type": None,
                "summary": "",
                "error": "Gemini returned an unsupported issue type."
            }

        return {
            "success": True,
            "issue_type": result["issue_type"],
            "summary": result.get("summary", ""),
            "error": None
        }

    except Exception as exc:
        return {
            "success": False,
            "issue_type": None,
            "summary": "",
            "error": str(exc)
        }