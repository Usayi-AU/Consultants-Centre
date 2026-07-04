import json
import os
from typing import Optional
from urllib import error, request


class ChatResponseError(RuntimeError):
    pass


class ChatService:
    def __init__(self, api_base: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None):
        self.api_base = api_base or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")

    def build_context(self, message: str, context: Optional[dict] = None) -> str:
        context = context or {}
        summary = []
        if context.get("dashboard"):
            summary.append(f"Dashboard: {context['dashboard']}")
        if context.get("dashboard_summary"):
            dashboard_summary = context["dashboard_summary"]
            summary.append(
                "Dashboard summary: "
                f"total reports: {dashboard_summary.get('total_reports', 'n/a')}; "
                f"submitted: {dashboard_summary.get('submitted', 'n/a')}; "
                f"reviewed: {dashboard_summary.get('reviewed', 'n/a')}; "
                f"sent to client: {dashboard_summary.get('sent', 'n/a')}; "
                f"pending: {dashboard_summary.get('pending', 'n/a')}"
            )
        if context.get("sent_report_clients"):
            summary.append("Sent report clients: " + "; ".join(context["sent_report_clients"][:10]))
        if context.get("projects"):
            summary.append("Projects: " + "; ".join(context["projects"][:5]))
        if context.get("reports"):
            summary.append("Reports: " + "; ".join(context["reports"][:5]))
        if context.get("documents"):
            summary.append("Documents: " + "; ".join(context["documents"][:5]))
        if context.get("proposals"):
            summary.append("Proposals: " + "; ".join(context["proposals"][:5]))

        context_block = "\n".join(summary)
        prompt = (
            "You are Consultancy Centre, the assistant for this consultancy dashboard. "
            "Answer questions specifically about the Consultancy Centre and the dashboard data you are given. "
            "When the user asks for counts, statuses, or client delivery numbers, use the exact numbers from the context and do not invent names or totals. "
            "If the relevant information is not present in the context, say that you cannot confirm it from the available dashboard data. "
            f"Use the context below when available.\n\nContext:\n{context_block or 'No additional context provided.'}\n\nUser question:\n{message}"
        )
        return prompt

    def generate(self, message: str, context: Optional[dict] = None) -> str:
        prompt = self.build_context(message, context)

        if self.api_key:
            return self._call_huggingface(prompt)

        try:
            return self._call_ollama(prompt)
        except Exception:
            return self._fallback_reply(message, context)

    def _call_ollama(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        try:
            data = self._http_post_json(f"{self.api_base}/api/generate", payload, timeout=20)
            return data.get("response", "").strip() or self._fallback_reply(prompt)
        except Exception:
            raise

    def _call_huggingface(self, prompt: str) -> str:
        data = self._http_post_json(
            f"https://api-inference.huggingface.co/models/{self.model}",
            {"inputs": prompt, "options": {"wait_for_model": True}},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=40,
        )
        if isinstance(data, list):
            return data[0].get("generated_text", "").strip() or self._fallback_reply(prompt)
        if isinstance(data, dict) and isinstance(data.get("generated_text"), str):
            return data["generated_text"].strip() or self._fallback_reply(prompt)
        raise ChatResponseError("Unexpected Hugging Face response")

    def _http_post_json(self, url: str, payload: dict, timeout: int = 20, headers: Optional[dict] = None):
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'ignore')}") from exc
        except error.URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc

    def _fallback_reply(self, message: str, context: Optional[dict] = None) -> str:
        context_summary = ", ".join((context or {}).get("projects", [])[:3]) if (context or {}).get("projects") else "your dashboard"
        return (
            "I’m here to help with consultancy questions. "
            f"For now I can offer a practical summary based on your dashboard context such as {context_summary or 'your dashboard'}. "
            "If you have Ollama running locally, I can provide richer answers from a free open-source model."
        )
