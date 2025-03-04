import os
from typing import Dict, List, Any, Type, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from backend.agents.debate_setter import DebateSetter
from backend.agents.debater_agent import DebaterAgent
from backend.agents.scorekeeper_agent import ScorekeeperAgent
from backend.data_sources.data_manager import DataManager
from backend.data_sources.fact_checker import FactChecker
import random
from pydantic import BaseModel, Field
from config import OPENROUTER_MODEL


class DebateState(BaseModel):
    """Represents the state of the debate."""
    topic: str = Field(description="The topic of the debate.")
    background_info: str = Field(description="Background information on the topic.")
    current_round: int = Field(default=0, description="The current round number.")
    max_rounds: int = Field(description="The maximum number of rounds.")
    introduction: str = Field(default="", description="The introduction to the debate.")
    rounds: List[Dict[str, Any]] = Field(default_factory=list, description="A list of debate rounds.")
    pro_conclusion: str = Field(default="", description="The pro side's conclusion.")
    con_conclusion: str = Field(default="", description="The con side's conclusion.")
    evaluation: str = Field(default="", description="The evaluation of the debate.")
    winner: Optional[str] = Field(default=None, description="The winner of the debate.")
    pro_score: int = Field(default=0, description="The pro side's score.")
    con_score: int = Field(default=0, description="The con side's score.")
    # Fact-checking results are stored within each round's data.


class DebateManager:
    """Manages the debate process between AI agents."""
    def __init__(self, topic: str, model_name: str = OPENROUTER_MODEL, num_rounds: int = 3):
        self.topic = topic
        self.model_name = model_name
        self.num_rounds = num_rounds
        self.data_manager = DataManager()
        self.fact_checker = FactChecker()

        # Get background information on the topic
        self.background_info = self.data_manager.get_topic_background(topic)

        # Initialize LLM
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model_name=model_name
        )

        # Create agents
        self.debate_setter = DebateSetter(self.llm, self.topic, self.background_info)

        # Create debater agents
        self.pro_agent = DebaterAgent(
            llm=self.llm,
            name=f"Pro-{random.choice(['Socrates', 'Aristotle', 'Plato', 'Kant', 'Locke'])}",
            stance="pro",
            topic=topic,
            background_info=self.background_info
        )

        self.con_agent = DebaterAgent(
            llm=self.llm,
            name=f"Con-{random.choice(['Nietzsche', 'Hume', 'Russell', 'Rousseau', 'Mill'])}",
            stance="con",
            topic=topic,
            background_info=self.background_info
        )

        self.scorekeeper = ScorekeeperAgent(self.llm)

        # Create debate graph
        self.graph = self._create_debate_graph()

    def _create_debate_graph(self) -> StateGraph:
        """Create the debate flow graph using LangGraph."""

        # Create the graph with a properly defined dictionary schema instead of just Dict
        from typing import Annotated, TypedDict
        
        class DebateStateDict(TypedDict, total=False):
            topic: str
            background_info: str
            current_round: int
            max_rounds: int
            introduction: str
            rounds: List[Dict[str, Any]]
            pro_conclusion: str
            con_conclusion: str
            evaluation: str
            winner: Optional[str]
            pro_score: int
            con_score: int
            
        # Use the properly defined schema
        graph = StateGraph(DebateStateDict)

        # Add nodes
        graph.add_node("set_debate", self.debate_setter.set_debate)
        graph.add_node("generate_pro_argument", self.pro_agent.generate_argument)
        graph.add_node("generate_con_argument", self.con_agent.generate_argument)
        graph.add_node("check_pro_facts", self.fact_check_pro)
        graph.add_node("check_con_facts", self.fact_check_con)
        graph.add_node("pro_conclusion_node", self.pro_agent.generate_conclusion)
        graph.add_node("con_conclusion_node", self.con_agent.generate_conclusion)
        graph.add_node("evaluate_debate", self.scorekeeper.evaluate_debate)

        # Define edges (these can stay the same, as they refer to the NODE names)
        graph.add_edge("set_debate", "generate_pro_argument")
        graph.add_edge("generate_pro_argument", "check_pro_facts")
        graph.add_edge("check_pro_facts", "generate_con_argument")
        graph.add_edge("generate_con_argument", "check_con_facts")

        # Conditional edge from check_con_facts
        graph.add_conditional_edges(
            "check_con_facts",
            self._check_round_completion,
            {
                "next_round": "generate_pro_argument",
                "finish_rounds": "pro_conclusion_node"
            }
        )

        graph.add_edge("pro_conclusion_node", "con_conclusion_node")
        graph.add_edge("con_conclusion_node", "evaluate_debate")
        graph.add_edge("evaluate_debate", END)

        # Set the entry point
        graph.set_entry_point("set_debate")

        return graph

    def _check_round_completion(self, state: Dict[str, Any]) -> str:
        """Check if all debate rounds have been completed."""
        current_round = state.get("current_round", 0)
        max_rounds = state.get("max_rounds", 0)
        
        if current_round < max_rounds:
            return "next_round"
        else:
            return "finish_rounds"

    def fact_check_pro(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fact check the pro debater's argument."""
        # Use .get() for safer access with defaults
        current_round = state.get("current_round", 0)
        rounds = state.get("rounds", [])
        
        if current_round < len(rounds):
            # Safely access argument with .get()
            round_data = rounds[current_round]
            argument = round_data.get("pro_argument", "")
            
            if not argument:
                return {}  # No argument to check
                
            fact_check_result = self.fact_checker.check_facts(argument)
            
            # Create a copy of the rounds list
            new_rounds = list(rounds)
            
            # Create a copy of the specific round dictionary
            round_data = dict(new_rounds[current_round])
            
            # Add the fact check result
            round_data["pro_fact_check"] = fact_check_result
            
            # Update the round in the list
            new_rounds[current_round] = round_data
            
            # Return an update dictionary with the modified rounds
            return {"rounds": new_rounds}
        return {}

    def fact_check_con(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fact check the con debater's argument."""
        # Use .get() for safer access with defaults
        current_round = state.get("current_round", 0)
        rounds = state.get("rounds", [])
        
        if current_round < len(rounds):
            # Safely access argument with .get()
            round_data = rounds[current_round]
            argument = round_data.get("con_argument", "")
            
            if not argument:
                return {}  # No argument to check
                
            fact_check_result = self.fact_checker.check_facts(argument)
            
            # Create a copy of the rounds list
            new_rounds = list(rounds)
            
            # Create a copy of the specific round dictionary
            round_data = dict(new_rounds[current_round])
            
            # Add the fact check result
            round_data["con_fact_check"] = fact_check_result
            
            # Update the round in the list
            new_rounds[current_round] = round_data
            
            # Return both the modified rounds and the incremented current_round
            return {
                "rounds": new_rounds,
                "current_round": current_round + 1
            }
        return {}

    def run_debate(self) -> Dict[str, Any]:
        """Run the debate and return the results."""
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
        
        # Pass the initial state dictionary directly to invoke
        result = app.invoke(initial_state)
        return result