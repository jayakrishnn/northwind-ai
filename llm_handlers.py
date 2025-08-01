import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)


# ✅ Format prompt to guide Gemini better
def format_mcp_prompt(user_query: str) -> str:
    return f"""
You are connected to the Northwind OData service.
Translate the user's natural language query into a valid OData URL query.

Return only the part after the base URL:
Example: If the full URL is https://services.odata.org/V4/Northwind/Northwind.svc/Customers?$filter=Country eq 'Germany',
just return: Customers?$filter=Country eq 'Germany'

Do not return explanation or markdown.

User query: "{user_query}"
"""

# ✅ Sanitize Gemini output
def sanitize_odata_query(text: str) -> str:
    query = text.strip().strip("`").replace("\n", "")

    # Close unbalanced single quotes
    if query.count("'") % 2 != 0:
        query += "'"

    return query


# ✅ Main LLM handler
async def generate_with_llm(query: str, model: str) -> str:
    if model == "gemini":
        prompt = format_mcp_prompt(query)

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)

            print("🔹 Raw Gemini output:", repr(response.text))

            sanitized = sanitize_odata_query(response.text)
            print("🔹 Sanitized OData query:", sanitized)

            return sanitized
        except Exception as e:
            raise Exception(f"❌ LLM Query Failed: {e}")

    else:
        raise Exception("Unsupported LLM model selected.")
