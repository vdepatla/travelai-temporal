"""
Workflow Registry - Central registry for all LangGraph workflows
"""

from src.workflow.search_flights_workflow import SearchFlightsAgentWorkflow
from src.workflow.book_accommodation_workflow import BookAccommodationAgentWorkflow
from src.workflow.create_itinerary_workflow import CreateItineraryAgentWorkflow


class WorkflowRegistry:
    """Registry to manage and instantiate workflows"""
    
    _workflows = {
        "search_flights": SearchFlightsAgentWorkflow,
        "book_accommodation": BookAccommodationAgentWorkflow,
        "create_itinerary": CreateItineraryAgentWorkflow,
    }
    
    @classmethod
    def get_workflow(cls, workflow_name: str):
        """Get a workflow instance by name"""
        if workflow_name not in cls._workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        return cls._workflows[workflow_name]()
    
    @classmethod
    def list_workflows(cls):
        """List all available workflows"""
        return list(cls._workflows.keys())
    
    @classmethod
    def register_workflow(cls, name: str, workflow_class):
        """Register a new workflow"""
        cls._workflows[name] = workflow_class
