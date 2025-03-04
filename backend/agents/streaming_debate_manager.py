from typing import Dict, Any, Iterator, Optional, Callable, List
from backend.agents.debate_manager import DebateManager
import threading
import time
import copy
from queue import Queue

class StreamingDebateManager(DebateManager):
    """Extends DebateManager to provide real-time streaming of debate progress."""
    
    def __init__(self, topic: str, model_name: str, num_rounds: int = 3):
        super().__init__(topic, model_name, num_rounds)
        self.debate_state = None
        self._debate_complete = False
        self._debate_lock = threading.Lock()
        self._debate_thread = None
        self._update_queue = Queue()
        self._current_phase = None
        self._error_state = None
        self._start_time = None 
        
    def start_debate_async(self):
        """Start the debate in a background thread."""
        if self._debate_thread and self._debate_thread.is_alive():
            return  # Debate already running
        
        self._debate_complete = False
        self._debate_thread = threading.Thread(target=self._run_debate_thread)
        self._debate_thread.daemon = True  # Make thread exit when main program exits
        self._debate_thread.start()
    
    def _run_debate_thread(self):
        """Run the debate in a background thread."""
        self._start_time = time.time()
        try:
            app = self.graph.compile()
            
            # Create initial state
            initial_state = {
                "topic": self.topic,
                "background_info": self.background_info,
                "max_rounds": self.num_rounds,
                "current_round": 0,
                "introduction": "",
                "rounds": [],
                "pro_conclusion": "",
                "con_conclusion": "",
                "evaluation": "",
                "winner": None,
                "pro_score": 0,
                "con_score": 0
            }
            
            # Initialize the state
            with self._debate_lock:
                self.debate_state = copy.deepcopy(initial_state)
                self._current_phase = "initializing"
            
            # Create a tracking variable for round data
            tracked_state = copy.deepcopy(initial_state)
            
            # Use a simpler approach with step-by-step execution and manual tracking
            try:
                # Run with timeout
                result = self._run_with_timeout(
                    lambda: app.invoke(initial_state),
                    timeout=600  # 10 minute timeout
                )
                
                if result:
                    self._queue_state_updates(tracked_state, result)
                    with self._debate_lock:
                        self.debate_state = result
                        self._debate_complete = True
                else:
                    self._error_state = "Debate timed out"
                    
            except Exception as e:
                self._error_state = f"Error in debate execution: {str(e)}"
                self._debate_complete = True
                        
        except Exception as e:
            self._error_state = f"Error initializing debate: {str(e)}"
            self._debate_complete = True
        finally:
            self._debate_complete = True

    def _run_with_timeout(self, func, timeout):
        """Run a function with timeout."""
        result = None
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                self._current_phase = "executing"
                result = func()
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            self._current_phase = "timeout"
            return None
        if exception:
            raise exception
        return result

    def _queue_state_updates(self, old_state: Dict[str, Any], new_state: Dict[str, Any]):
        """Compare old and new states to determine updates and queue them."""
        try:
            # Check introduction
            if old_state.get("introduction", "") != new_state.get("introduction", "") and new_state.get("introduction"):
                self._current_phase = "introduction"
                self._update_queue.put({
                    "type": "introduction", 
                    "content": new_state["introduction"]
                })
            
            # Check rounds
            old_rounds = old_state.get("rounds", [])
            new_rounds = new_state.get("rounds", [])
            
            for i, round_data in enumerate(new_rounds):
                if i >= len(old_rounds):
                    # New round started
                    self._current_phase = f"round_{i+1}"
                    
                    # Queue updates for this round
                    for update_type in ["pro_argument", "pro_fact_check", "con_argument", "con_fact_check"]:
                        if update_type in round_data:
                            self._update_queue.put({
                                "type": update_type,
                                "round": i + 1,
                                "content": round_data[update_type]
                            })
                else:
                    # Check for updates to existing round
                    for update_type in ["pro_argument", "pro_fact_check", "con_argument", "con_fact_check"]:
                        if (update_type in round_data and 
                            round_data[update_type] != old_rounds[i].get(update_type, "")):
                            self._update_queue.put({
                                "type": update_type,
                                "round": i + 1,
                                "content": round_data[update_type]
                            })
            
            # Check conclusions
            for conclusion_type in ["pro_conclusion", "con_conclusion"]:
                if (new_state.get(conclusion_type) and 
                    new_state[conclusion_type] != old_state.get(conclusion_type, "")):
                    self._current_phase = conclusion_type
                    self._update_queue.put({
                        "type": conclusion_type,
                        "content": new_state[conclusion_type]
                    })
            
            # Check evaluation
            if new_state.get("evaluation") and new_state["evaluation"] != old_state.get("evaluation", ""):
                self._current_phase = "evaluation"
                self._update_queue.put({
                    "type": "evaluation",
                    "content": new_state["evaluation"],
                    "winner": new_state.get("winner"),
                    "pro_score": new_state.get("pro_score"),
                    "con_score": new_state.get("con_score")
                })
                
        except Exception as e:
            self._error_state = f"Error queuing updates: {str(e)}"
            print(f"Error in _queue_state_updates: {e}")

    def get_current_state(self) -> Dict[str, Any]:
        """Get the current debate state."""
        with self._debate_lock:
            if self.debate_state:
                return copy.deepcopy(self.debate_state)
            return {"topic": self.topic, "status": "Initializing..."}
    
    def get_updates(self) -> List[Dict[str, Any]]:
        """Get any new updates from the queue."""
        updates = []
        while not self._update_queue.empty():
            try:
                update = self._update_queue.get(block=False)
                updates.append(update)
            except:
                break
        return updates
    
    def is_complete(self) -> bool:
        """Check if the debate is complete."""
        return self._debate_complete
    
    def stream_debate(self, interval: float = 0.5) -> Iterator[Dict[str, Any]]:
        """Stream the debate state as it progresses."""
        last_state = None
        
        while not self.is_complete() or last_state != self.debate_state:
            current_state = self.get_current_state()
            if current_state != last_state:
                yield current_state
                last_state = copy.deepcopy(current_state)
            time.sleep(interval)
        
        # One final yield to ensure we get the final state
        yield self.get_current_state()

    def get_debate_status(self) -> Dict[str, Any]:
        """Get current debate status including any errors."""
        with self._debate_lock:
            return {
                "complete": self._debate_complete,
                "current_phase": self._current_phase,
                "error": self._error_state,
                "duration": time.time() - (self._start_time or time.time()),
                "has_updates": not self._update_queue.empty()
            }
