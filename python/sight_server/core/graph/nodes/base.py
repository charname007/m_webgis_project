from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


@dataclass
class NodeContext:
    sql_generator: Any
    sql_executor: Any
    result_parser: Any
    answer_generator: Any
    schema_fetcher: Any = None
    llm: Any = None
    error_handler: Any = None
    cache_manager: Any = None
    structured_logger: Any = None
    result_validator: Any = None
    data_analyzer: Any = None


class NodeBase:
    """Base class providing shared context and logger."""

    def __init__(self, context: NodeContext) -> None:
        self.context = context
        self.logger = logging.getLogger(self.__class__.__module__)

    @property
    def sql_generator(self) -> Any:
        return self.context.sql_generator

    @property
    def sql_executor(self) -> Any:
        return self.context.sql_executor

    @property
    def result_parser(self) -> Any:
        return self.context.result_parser

    @property
    def answer_generator(self) -> Any:
        return self.context.answer_generator

    @property
    def schema_fetcher(self) -> Any:
        return self.context.schema_fetcher

    @property
    def llm(self) -> Any:
        return self.context.llm

    @property
    def error_handler(self) -> Any:
        return self.context.error_handler

    @property
    def cache_manager(self) -> Any:
        return self.context.cache_manager

    @property
    def structured_logger(self) -> Any:
        return self.context.structured_logger

    @property
    def result_validator(self) -> Any:
        return self.context.result_validator

    @property
    def data_analyzer(self) -> Any:
        return self.context.data_analyzer
