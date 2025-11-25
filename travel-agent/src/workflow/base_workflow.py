import openai
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from src.workflow.constants import AGENTIC_GOAL, DEFAULT_LLM_MODEL

T = TypeVar('T')


class BaseWorkflowState:
    """Base state class for all workflows"""
    def __init__(self):
        self.messages: list = []
        self.function_args: dict = {}
        self.error: str = None
        self.llm_response = None


class BaseLangGraphWorkflow(ABC, Generic[T]):
    """Base class for all LangGraph workflows"""
    
    def __init__(self, goal: str, function_definition: Dict[str, Any]):
        self.goal = goal
        self.function_definition = function_definition
        self.workflow = self._create_workflow()

    @abstractmethod
    def _create_workflow(self) -> CompiledStateGraph:
        """Create the workflow graph - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _prepare_request(self, state: BaseWorkflowState) -> BaseWorkflowState:
        """Prepare the request - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _create_final_result(self, state: BaseWorkflowState) -> BaseWorkflowState:
        """Create the final result - must be implemented by subclasses"""
        pass

    async def _call_llm(self, state: BaseWorkflowState) -> BaseWorkflowState:
        """Standard LLM calling logic"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=DEFAULT_LLM_MODEL,
                messages=state.messages,
                functions=[self.function_definition],
                api_key=os.getenv("OPENAI_API_KEY")
            )
            state.llm_response = response
        except Exception as e:
            state.error = str(e)
        return state

    async def _process_response(self, state: BaseWorkflowState) -> BaseWorkflowState:
        """Standard response processing logic"""
        if state.error:
            return state
            
        choice = state.llm_response.choices[0]
        if choice.finish_reason == "function_call":
            import json
            state.function_args = json.loads(choice.message.function_call.arguments)
        return state

    def _prepare_system_message(self) -> str:
        """Prepare the system message with agentic goal"""
        return f"{AGENTIC_GOAL}\n\nSpecific goal: {self.goal}"

    @abstractmethod
    async def run(self, *args, **kwargs) -> T:
        """Run the workflow - must be implemented by subclasses"""
        pass
