from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Union, Generic, TypeVar
import msgspec
from litestar.types import Empty

T = TypeVar("T", bound=msgspec.Struct)

class BaseTool(ABC, Generic[T]):
    """
    Abstract base class for all tools.
    """
    name: str = ""
    description: str = ""
    args_schema: Type[T] | None = None

    def __init__(self):
        if not self.name:
            raise ValueError("Tool name must be defined")
        if not self.description:
            raise ValueError("Tool description must be defined")

    @abstractmethod
    async def run(self, args: T) -> Any:
        """
        Execute the tool logic.
        """
        pass

    def validate_args(self, args: Dict[str, Any]) -> T:
        """
        Validate arguments using msgspec based on defined schema.
        """
        if self.args_schema is None:
            return Empty # type: ignore

        try:
            return msgspec.convert(args, self.args_schema)
        except msgspec.ValidationError as e:
            raise ValueError(f"Invalid arguments for tool {self.name}: {e}")

    def to_schema(self) -> Dict[str, Any]:
        """
        Convert tool definition to OpenAI function schema.
        """
        # This is a simplified schema generation. 
        # For production use, a more robust generation based on msgspec or pydantic is needed.
        # For now, we will assume args_schema is a msgspec.Struct and inspect it lightly or manual define.
        # In a real implementation with msgspec, we'd inspect the struct definition.
        
        # NOTE: For simplicity in this demo, we might rely on manual schema definition or basic introspection.
        # We will implement a basic introspection helper later.
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                # "parameters": ... # To be implemented via introspection
            }
        }
