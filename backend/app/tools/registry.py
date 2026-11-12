"""Tool registry and execution sandbox with strict Pydantic argument validation."""
from typing import Any, Callable, Dict, Type
from pydantic import BaseModel
from app.core.exceptions import AgentraException


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Type[BaseModel]
    handler: Any


class ToolRegistry:
    """Registry maintaining approved tools and executing them with schema validation."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Type[BaseModel],
        handler: Callable[..., Any],
    ) -> None:
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Validates arguments against schema and executes approved tool."""
        if tool_name not in self._tools:
            raise AgentraException(
                code="TOOL_NOT_PERMITTED",
                message=f"Tool '{tool_name}' is not in the approved tool allowlist.",
                status_code=403,
            )

        tool = self._tools[tool_name]
        try:
            validated_input = tool.input_schema.model_validate(arguments)
        except Exception as e:
            raise AgentraException(
                code="INVALID_TOOL_ARGUMENTS",
                message=f"Tool '{tool_name}' arguments failed validation: {str(e)}",
                status_code=400,
            )

        return tool.handler(validated_input)
