from __future__ import annotations

import time
from typing import Any, Dict, List, Set

from ...schemas import AgentState
from ...prompts import PromptManager
from .base import NodeBase


class FetchSchemaNode(NodeBase):
    """Fetch database schema and inject it into dependent LLM instances."""

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        if state.get("schema_fetched"):
            self.logger.info("[Node: fetch_schema] Schema already fetched, skipping")
            return {}

        self.logger.info("[Node: fetch_schema] Fetching database schema...")

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                schema: Dict[str, Any] = self.schema_fetcher.fetch_schema(use_cache=True)

                if "error" in schema:
                    self.logger.warning(
                        "[Node: fetch_schema] Attempt %s/%s failed: %s",
                        retry_count + 1,
                        max_retries,
                        schema["error"],
                    )

                    if retry_count < max_retries - 1:
                        retry_count += 1
                        time.sleep(1)
                        continue

                    return self._failure_state(schema["error"], retry_count + 1)

                tables = schema.get("tables", {})
                if not tables:
                    self.logger.warning(
                        "[Node: fetch_schema] No tables found in schema, attempt %s/%s",
                        retry_count + 1,
                        max_retries,
                    )

                    if retry_count < max_retries - 1:
                        retry_count += 1
                        time.sleep(1)
                        continue

                    return self._failure_state("未找到任何表信息", retry_count + 1)

                formatted_schema = self.schema_fetcher.format_schema_for_llm(schema)
                system_prompt = PromptManager.build_system_prompt_with_schema(formatted_schema)

                injected = self._inject_schema_into_llms(formatted_schema, system_prompt)

                thought_step = {
                    "step": 0,
                    "type": "schema_fetch",
                    "action": "fetch_database_schema",
                    "output": {
                        "table_count": len(tables),
                        "spatial_table_count": len(schema.get("spatial_tables", {})),
                        "retry_count": retry_count + 1,
                        "schema_length": len(formatted_schema),
                        "system_context_updated": injected,
                        "system_prompt_updated": injected,
                    },
                    "status": "completed",
                }

                return {
                    "database_schema": schema,
                    "formatted_schema": formatted_schema,
                    "schema_fetched": True,
                    "thought_chain": [thought_step],
                }

            except Exception as exc:
                self.logger.warning(
                    "[Node: fetch_schema] Attempt %s/%s failed with exception: %s",
                    retry_count + 1,
                    max_retries,
                    exc,
                )

                if retry_count < max_retries - 1:
                    retry_count += 1
                    time.sleep(1)
                    continue

                return self._failure_state(str(exc), retry_count + 1)

        return self._failure_state("未知错误", max_retries)

    def _inject_schema_into_llms(self, formatted_schema: str, system_prompt: str) -> bool:
        updated_any = False
        registry: List[tuple[str, Any]] = []

        if hasattr(self.sql_generator, "set_database_schema"):
            self.sql_generator.set_database_schema(formatted_schema)

        if hasattr(self.sql_generator, "llm"):
            registry.append(("SQLGenerator", self.sql_generator.llm))
        if self.llm is not None:
            registry.append(("AgentLLM", self.llm))
        if hasattr(self.answer_generator, "llm"):
            registry.append(("AnswerGenerator", self.answer_generator.llm))

        seen: Set[int] = set()
        for name, llm_instance in registry:
            if not llm_instance:
                continue
            instance_id = id(llm_instance)
            if instance_id in seen:
                continue
            seen.add(instance_id)

            if hasattr(llm_instance, "update_system_context"):
                llm_instance.update_system_context({"database_schema": formatted_schema})
                updated_any = True
            if hasattr(llm_instance, "set_system_prompt"):
                llm_instance.set_system_prompt(system_prompt)
                updated_any = True

            self.logger.info(
                "[Node: fetch_schema] Injected schema into %s", name
            )

        return updated_any

    def _failure_state(self, error_message: str, retry_count: int) -> Dict[str, Any]:
        return {
            "database_schema": None,
            "schema_fetched": False,
            "thought_chain": [
                {
                    "step": 0,
                    "type": "schema_fetch",
                    "action": "fetch_database_schema",
                    "error": error_message,
                    "retry_count": retry_count,
                    "status": "failed",
                }
            ],
        }
