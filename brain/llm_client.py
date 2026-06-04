# [WFGY] Zone: SAFE | λ: 0.3 | Action: LLM Client Interface and implementations
import json
import urllib.request
import urllib.error
from abc import ABC, abstractmethod

class LLMClient(ABC):
    """
    Abstract Base Class for LLM API wrappers.
    """
    @abstractmethod
    def generate_completion(self, system_prompt: str, user_prompt: str, schema: dict = None) -> str:
        pass

class OpenAICompatibleClient(LLMClient):
    """
    Client for OpenAI-compatible endpoints (LM Studio, Ollama, OpenAI).
    """
    def __init__(self, base_url: str, model: str, api_key: str = "unused", disable_json_format: bool = False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.disable_json_format = disable_json_format

    def generate_completion(self, system_prompt: str, user_prompt: str, schema: dict = None) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }
        
        if not self.disable_json_format:
            if schema:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_response",
                        "schema": schema
                    }
                }
            else:
                # If no schema is provided, use a generic json schema to stay compatible with LM Studio (which rejects type: json_object)
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "generic_object",
                        "schema": {
                            "type": "object",
                            "additionalProperties": True
                        }
                    }
                }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            print(f"[LLM] Contacting OpenAI compatible endpoint at {url} (model: {self.model})...")
            with urllib.request.urlopen(req, timeout=180) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                return res_json["choices"][0]["message"]["content"]
        except urllib.error.URLError as e:
            # Fallback retry without JSON format if server rejected it
            print(f"[LLM] Connection error or JSON schema not supported, retrying without strict format... Detail: {e}")
            if isinstance(e, urllib.error.HTTPError):
                try:
                    err_body = e.read().decode("utf-8", errors="ignore")
                    print(f"[LLM ERROR DETAIL] {err_body}")
                except Exception:
                    pass
            if "response_format" in payload:
                del payload["response_format"]
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=180) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)
                    return res_json["choices"][0]["message"]["content"]
            except Exception as e_inner:
                raise RuntimeError(f"LLM API request failed: {e_inner}")
        except Exception as e:
            raise RuntimeError(f"LLM API request failed: {e}")

class GeminiAPIClient(LLMClient):
    """
    Client for native Google Gemini API using HTTPS requests.
    """
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def clean_schema_for_gemini(self, schema):
        if not isinstance(schema, dict):
            return schema
        cleaned = {}
        for k, v in schema.items():
            if k == "additionalProperties":
                continue
            if isinstance(v, dict):
                cleaned[k] = self.clean_schema_for_gemini(v)
            elif isinstance(v, list):
                cleaned[k] = [self.clean_schema_for_gemini(item) if isinstance(item, dict) else item for item in v]
            else:
                cleaned[k] = v
        return cleaned

    def generate_completion(self, system_prompt: str, user_prompt: str, schema: dict = None) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Instructions:\n{system_prompt}\n\nUser Prompt:\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        if schema:
            payload["generationConfig"]["responseSchema"] = self.clean_schema_for_gemini(schema)

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            print(f"[LLM] Contacting Gemini endpoint...")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                candidate = res_json["candidates"][0]
                text = candidate["content"]["parts"][0]["text"]
                return text
        except urllib.error.HTTPError as he:
            try:
                err_body = he.read().decode("utf-8", errors="ignore")
                print(f"[GEMINI LLM ERROR DETAIL] {err_body}")
            except Exception:
                err_body = str(he)
            raise RuntimeError(f"Gemini API request failed: {he} - Details: {err_body}")
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}")
