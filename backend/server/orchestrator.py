import logging
from enum import Enum
import json
import os
from datetime import datetime

from backend.server.llm_api_client import llm_api_client

# Configure logging
logger = logging.getLogger(__name__)

class DebateStage(Enum):
    """Enum representing the various stages of a debate."""
    INITIALIZED = "initialized"
    PREPARING = "preparing"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DebateOrchestrator:
    """Orchestrates the debate process."""
    
    def __init__(self, debate_id: str, topic: str, human_side: str):
        self.debate_id = debate_id
        self.topic = topic
        self.human_side = human_side
        self.ai_side = "pro" if human_side == "con" else "con"
        self.storage_dir = os.path.join("data", "debates", debate_id)
        self.stage = DebateStage.INITIALIZED
        self.arguments = {
            "pro": None,
            "con": None
        }
        self._ensure_storage_directory()
        self._save_debate_state()
    
    def _ensure_storage_directory(self):
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"Ensured storage directory exists: {self.storage_dir}")
    
    def _save_debate_state(self):
        """Save the current state of the debate."""
        state_file = os.path.join(self.storage_dir, "state.json")
        state = {
            "debate_id": self.debate_id,
            "topic": self.topic,
            "human_side": self.human_side,
            "ai_side": self.ai_side,
            "stage": self.stage.value,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.debug(f"Saved debate state: {state}")

    async def prepare_debate(self):
        """Prepare the debate by generating arguments for both sides."""
        logger.info(f"[Debate ID: {self.debate_id}] Starting debate preparation")
        
        try:
            # Update stage
            self.stage = DebateStage.PREPARING
            self._save_debate_state()
            
            # Generate arguments for the AI side
            logger.info(f"[Debate ID: {self.debate_id}] Generating arguments for AI side: {self.ai_side}")
            ai_arguments = await self._generate_arguments(self.ai_side)
            logger.info(f"[Debate ID: {self.debate_id}] AI arguments generated successfully")
            
            # Store the generated arguments
            logger.info(f"[Debate ID: {self.debate_id}] Storing AI arguments")
            self._store_arguments(self.ai_side, ai_arguments)
            logger.info(f"[Debate ID: {self.debate_id}] AI arguments stored successfully")
            
            # Generate suggested arguments for the human side
            logger.info(f"[Debate ID: {self.debate_id}] Generating suggested arguments for human side: {self.human_side}")
            human_suggested_arguments = await self._generate_arguments(self.human_side)
            logger.info(f"[Debate ID: {self.debate_id}] Human suggested arguments generated successfully")
            
            # Store the suggested arguments
            logger.info(f"[Debate ID: {self.debate_id}] Storing suggested arguments for human")
            self._store_arguments(self.human_side, human_suggested_arguments)
            logger.info(f"[Debate ID: {self.debate_id}] Human suggested arguments stored successfully")
            
            # Update stage
            self.stage = DebateStage.READY
            self._save_debate_state()
            
            logger.info(f"[Debate ID: {self.debate_id}] Debate preparation completed")
            return {"status": "success", "stage": self.stage.value}
            
        except Exception as e:
            logger.error(f"[Debate ID: {self.debate_id}] Preparation failed: {str(e)}", exc_info=True)
            self.stage = DebateStage.FAILED
            self._save_debate_state()
            raise

    async def _generate_arguments(self, side):
        """Generate arguments for a specific side using the LLM API."""
        logger.info(f"[Debate ID: {self.debate_id}] Sending request to LLM API for {side} arguments")
        prompt = self._create_argument_prompt(side)
        
        try:
            response = await llm_api_client.generate_arguments(prompt)
            logger.info(f"[Debate ID: {self.debate_id}] Received response from LLM API for {side}")
            return response
        except Exception as e:
            logger.error(f"[Debate ID: {self.debate_id}] Error generating arguments for {side}: {str(e)}")
            raise

    def _create_argument_prompt(self, side):
        """Create a prompt for generating arguments for a specific side."""
        stance = "for" if side == "pro" else "against"
        prompt = f"Generate strong, logical arguments {stance} the following topic: '{self.topic}'. "
        prompt += "Include 3-5 key points with supporting evidence and reasoning."
        return prompt

    def _store_arguments(self, side, arguments):
        """Store arguments for a specific side."""
        self.arguments[side] = arguments
        
        # Save to file system
        arguments_file = os.path.join(self.storage_dir, f"{side}_arguments.txt")
        with open(arguments_file, 'w') as f:
            f.write(arguments)
        
        logger.debug(f"Stored {side} arguments to {arguments_file}")

    def get_debate_status(self):
        """Get the current status of the debate."""
        return {
            "debate_id": self.debate_id,
            "topic": self.topic,
            "human_side": self.human_side,
            "ai_side": self.ai_side,
            "stage": self.stage.value,
            "has_human_arguments": self.arguments[self.human_side] is not None,
            "has_ai_arguments": self.arguments[self.ai_side] is not None
        }
