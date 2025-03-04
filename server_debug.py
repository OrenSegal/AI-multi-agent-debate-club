import asyncio
import uuid
import logging
from backend.api.routes import handle_debate_orchestration
from backend.api.models import DebateParams
from backend.server.workflow_manager import DebateWorkflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_debate_orchestration():
    """Test the debate orchestration process directly."""
    logger.info("Starting test debate orchestration...")
    
    debate_params = DebateParams(
        debate_id=str(uuid.uuid4()),
        topic="Is artificial intelligence beneficial for humanity?",
        human_side="con"
    )
    
    logger.info(f"Created test debate with ID: {debate_params.debate_id}")
    logger.info(f"Topic: {debate_params.topic}")
    logger.info(f"Human side: {debate_params.human_side}")
    
    try:
        logger.info("Calling handle_debate_orchestration...")
        await handle_debate_orchestration(debate_params)
        logger.info("Debate orchestration completed successfully")
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_workflow():
    """Test the workflow manager."""
    logger.info("Testing workflow manager...")
    
    # Create a sample workflow
    workflow = DebateWorkflow()
    
    # Add some tasks
    async def task1(param1, **kwargs):
        logger.info(f"Executing task1 with param1={param1}")
        await asyncio.sleep(1)  # Simulate work
        return f"Result from task1: {param1}"
    
    async def task2(param2, **kwargs):
        logger.info(f"Executing task2 with param2={param2}")
        await asyncio.sleep(1.5)  # Simulate work
        return f"Result from task2: {param2}"
    
    async def task3(task1_result, task2_result, **kwargs):
        logger.info(f"Executing task3 with previous results: {task1_result}, {task2_result}")
        await asyncio.sleep(0.5)  # Simulate work
        return f"Final result: {task1_result} + {task2_result}"
    
    workflow.add_task("task1", task1)
    workflow.add_task("task2", task2)
    workflow.add_task("task3", task3, dependencies=["task1", "task2"])
    
    # Execute the workflow
    try:
        result = await workflow.execute_workflow(param1="Hello", param2="World")
        logger.info(f"Workflow completed with result: {result}")
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("Running server debug script")
    
    # Run the tests
    asyncio.run(test_debate_orchestration())
    # asyncio.run(test_workflow())  # Uncomment to test the workflow manager
