from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ExecutionResult(BaseModel):
    success: bool
    action_taken: str
    output: str
    error: Optional[str] = None
    files_modified: list[str] = []
    metadata: Dict[str, Any] = {}


class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, action: str, context: Dict[str, Any]) -> ExecutionResult:
        pass
