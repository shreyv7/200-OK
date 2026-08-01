"""Amazon Bedrock failover provider. Owner: Backend.

Only file in the repo allowed to import boto3 (hard constraint,
guidelines.md §9.3 / techstack.md §11.1). AIA/AIS call
`LLMProvider.generate_structured()` through DI — never this class
directly.

Structured output uses the Bedrock Converse API's forced tool-use: the
target JSON schema is registered as the single tool's input schema and
`toolChoice` pins the model to call exactly that tool, so the response's
tool-use block already IS the parsed structured payload — no free-text
JSON parsing/repair needed. This is the same call shape across every
tool-use-capable Bedrock model family (Anthropic Claude, Amazon Nova,
etc.), which is why `bedrock_model_id` is the only per-model config this
class needs.

Untested against a live AWS account as of B3 (docs/work.md) — shipped
behind `BEDROCK_FAILOVER_ENABLED` (default off, see app/core/di.py) per
the ground rule "if we don't buy Bedrock yet, ship the failover code
behind a flag with a stub test." Wire a real account (region + model ID
+ IAM credentials boto3 can discover) and flip the flag to exercise this
for real; see docs/work.md §1.5 for the exact manual setup steps.
"""

from __future__ import annotations

from typing import Any

from app.providers.llm.base import LLMProvider, LLMProviderUnavailable

_TOOL_NAME = "emit_structured_output"

# Bedrock runtime error codes that mean "try again / try elsewhere", not
# "this request is broken". See botocore.exceptions.ClientError.response["Error"]["Code"].
_RETRYABLE_ERROR_CODES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "ModelTimeoutException",
    "ModelNotReadyException",
    "InternalServerException",
}


class BedrockLLMProvider(LLMProvider):
    def __init__(self, region: str | None, model_id: str | None) -> None:
        if not region or not model_id:
            raise RuntimeError(
                "BedrockLLMProvider requires both BEDROCK_REGION and BEDROCK_MODEL_ID"
            )
        self._region = region
        self._model_id = model_id
        self._client: Any | None = None

    def _bedrock_client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client("bedrock-runtime", region_name=self._region)
        return self._client

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from botocore.exceptions import ClientError

        bedrock_messages = [
            {"role": "assistant" if m["role"] == "assistant" else "user", "content": [{"text": m["content"]}]}
            for m in messages
            if m["role"] != "system"
        ]
        system_prompts = [{"text": m["content"]} for m in messages if m["role"] == "system"]

        tool_config = {
            "tools": [{"toolSpec": {"name": _TOOL_NAME, "inputSchema": {"json": schema}}}],
            "toolChoice": {"tool": {"name": _TOOL_NAME}},
        }

        call_kwargs: dict[str, Any] = {
            "modelId": self._model_id,
            "messages": bedrock_messages,
            "toolConfig": tool_config,
        }
        if system_prompts:
            call_kwargs["system"] = system_prompts

        client = self._bedrock_client()
        try:
            response = client.converse(**call_kwargs)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in _RETRYABLE_ERROR_CODES:
                raise LLMProviderUnavailable(f"Bedrock {code}: {exc}") from exc
            raise

        for block in response["output"]["message"]["content"]:
            tool_use = block.get("toolUse")
            if tool_use and tool_use.get("name") == _TOOL_NAME:
                return tool_use["input"]

        raise LLMProviderUnavailable(
            "Bedrock response did not include the expected tool-use block "
            f"(stopReason={response.get('stopReason')!r})"
        )
