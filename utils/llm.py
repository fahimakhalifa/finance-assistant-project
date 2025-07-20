import requests
import os

def call_groq_llm(prompt: str) -> str:
    import os
    api_key = "PUT_YOUR_API_KEY"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as err:
        return f"❌ HTTP Error: {err.response.status_code} — {err.response.text}"
    except Exception as e:
        return f"❌ LLM call failed: {str(e)}"
