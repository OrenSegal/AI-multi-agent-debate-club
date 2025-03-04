import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException

from backend.api.models import DebateParams
from backend.debate.orchestrator import DebateOrchestrator, DebateStage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("debate_api.log")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Debate Club API")

# In-memory store for active orchestrators
active_orchestrators: Dict[str, DebateOrchestrator] = {}

@app.post("/orchestrate_debate")
async def orchestrate_debate(debate_params: DebateParams, background_tasks: BackgroundTasks):
    """Start orchestrating a new debate"""
    logger.info(f"Received debate orchestration request: {debate_params}")
    
    # Check if debate already exists
    if debate_params.debate_id in active_orchestrators:
        logger.warning(f"Debate with ID {debate_params.debate_id} already exists")
        return {"message": "Debate already exists", "debate_id": debate_params.debate_id}
    
    # Create a new orchestrator
    orchestrator = DebateOrchestrator(
        debate_id=debate_params.debate_id,
        topic=debate_params.topic,
        human_side=debate_params.human_side
    )
    
    # Store in active orchestrators
    active_orchestrators[debate_params.debate_id] = orchestrator
    
    # Create a background task to handle the debate
    background_tasks.add_task(handle_debate_orchestration, debate_params)
    logger.info(f"Background task added for debate: {debate_params.debate_id}")
    
    return {
        "message": "Debate orchestration started", 
        "debate_id": debate_params.debate_id,
        "status": orchestrator.get_debate_status()
    }

async def handle_debate_orchestration(debate_params: DebateParams):
    """Handle the orchestration of a debate in the background."""
    logger.info(f"Starting debate orchestration for debate_id: {debate_params.debate_id}")
    
    orchestrator = active_orchestrators.get(debate_params.debate_id)
    if not orchestrator:
        logger.error(f"Orchestrator for debate {debate_params.debate_id} not found")
        return
    
    try:
        logger.info(f"Beginning debate preparation for {debate_params.debate_id}")
        await orchestrator.prepare_debate()
        logger.info(f"Debate preparation completed for {debate_params.debate_id}")
    except Exception as e:
        logger.error(f"Error in debate orchestration: {str(e)}")
        logger.error(traceback.format_exc())

@app.get("/debate/{debate_id}/status")
async def get_debate_status(debate_id: str):
    """Get the current status of a debate"""
    logger.info(f"Getting status for debate: {debate_id}")
    
    # Check if debate exists in active orchestrators
    if debate_id in active_orchestrators:
        return active_orchestrators[debate_id].get_debate_status()
    
    # Check if debate exists on disk
    state_file = os.path.join("data", "debates", debate_id, "state.json")
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    
    # Debate not found
    logger.warning(f"Debate {debate_id} not found")
    raise HTTPException(status_code=404, detail=f"Debate with ID {debate_id} not found")

@app.get("/debates")
async def list_debates():
    """List all debates"""
    logger.info("Listing all debates")
    
    debates = []
    
    # Get active debates
    for debate_id, orchestrator in active_orchestrators.items():
        debates.append(orchestrator.get_debate_status())
    
    # Get saved debates
    debates_dir = os.path.join("data", "debates")
    if os.path.exists(debates_dir):
        for debate_id in os.listdir(debates_dir):
            state_file = os.path.join(debates_dir, debate_id, "state.json")
            if os.path.exists(state_file) and debate_id not in active_orchestrators:
                with open(state_file, 'r') as f:
                    debates.append(json.load(f))
    
    return {"debates": debates}