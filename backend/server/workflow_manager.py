import logging
import asyncio
from enum import Enum
from typing import Dict, List, Any, Callable, Awaitable, Optional
import time

# Configure logging
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Status of a workflow task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowTask:
    """Represents a task in a workflow."""
    
    def __init__(self, name: str, func: Callable, dependencies: List[str] = None):
        self.name = name
        self.func = func
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
    
    async def execute(self, **kwargs):
        """Execute the task function."""
        try:
            logger.info(f"Starting task: {self.name}")
            self.status = TaskStatus.IN_PROGRESS
            self.start_time = time.time()
            
            # Execute the function
            self.result = await self.func(**kwargs)
            
            self.status = TaskStatus.COMPLETED
            self.end_time = time.time()
            logger.info(f"Completed task: {self.name} in {self.end_time - self.start_time:.2f}s")
            return self.result
        
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            self.end_time = time.time()
            logger.error(f"Task {self.name} failed after {self.end_time - self.start_time:.2f}s: {str(e)}")
            raise

class DebateWorkflow:
    """Manages the workflow for debate orchestration."""
    
    def __init__(self):
        self.tasks: Dict[str, WorkflowTask] = {}
        self.context = {}
    
    def add_task(self, name: str, func: Callable, dependencies: List[str] = None):
        """Add a task to the workflow."""
        self.tasks[name] = WorkflowTask(name, func, dependencies)
        logger.debug(f"Added task {name} to workflow")
    
    async def execute_workflow(self, **initial_context):
        """Execute the workflow tasks in dependency order."""
        self.context.update(initial_context)
        
        # Find tasks with no dependencies
        pending_tasks = [task for task in self.tasks.values() if not task.dependencies]
        completed_task_names = set()
        
        while pending_tasks:
            # Execute tasks in parallel if they have no unresolved dependencies
            tasks_to_execute = []
            for task in pending_tasks:
                if all(dep in completed_task_names for dep in task.dependencies):
                    tasks_to_execute.append(task)
            
            if not tasks_to_execute:
                logger.error("Deadlock detected in workflow execution")
                break
            
            # Execute eligible tasks in parallel
            results = await asyncio.gather(
                *(task.execute(**self.context) for task in tasks_to_execute),
                return_exceptions=True
            )
            
            # Process results
            for task, result in zip(tasks_to_execute, results):
                if isinstance(result, Exception):
                    logger.error(f"Task {task.name} failed: {str(result)}")
                    task.status = TaskStatus.FAILED
                    task.error = str(result)
                else:
                    completed_task_names.add(task.name)
                    self.context[task.name + "_result"] = result
            
            # Remove executed tasks from pending
            pending_tasks = [task for task in pending_tasks if task.name not in completed_task_names]
            
            # Add new eligible tasks
            for task_name, task in self.tasks.items():
                if (task.name not in completed_task_names and 
                    task.status == TaskStatus.PENDING and
                    task not in pending_tasks):
                    pending_tasks.append(task)
        
        # Return the final context
        return self.context
    
    def get_status(self):
        """Get the status of all tasks in the workflow."""
        return {
            task_name: {
                "status": task.status.value,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "error": task.error
            }
            for task_name, task in self.tasks.items()
        }
