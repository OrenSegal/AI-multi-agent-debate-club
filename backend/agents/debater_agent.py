from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

class DebaterAgent:
    """Agent that takes a stance (pro or con) on a debate topic."""
    
    def __init__(self, llm, name: str, stance: str, topic: str, background_info: str):
        self.llm = llm
        self.name = name
        self.stance = stance  # "pro" or "con"
        self.topic = topic
        self.background_info = background_info
        
        # Define prompts
        self.argument_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are {name}, an expert debater taking the {stance} position on the topic: "{topic}".
             
             You are participating in round {round_num} of a formal debate. Your objective is to present a compelling argument
             supporting your {stance} position.
             
             Guidelines:
             1. Make clear, logical arguments
             2. Use factual evidence to support your points
             3. Anticipate and address counterarguments
             4. Remain respectful but assertive
             5. Be concise but thorough
             
             Background information: {background_info}
             
             If this isn't your first round, consider the previous arguments:
             {previous_arguments}
             
             Craft a compelling argument of approximately 250-350 words.
             """),
            ("human", "Please provide your {stance} argument for round {round_num} on the topic: {topic}")
        ])
        
        self.conclusion_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are {name}, an expert debater who has been arguing the {stance} position on the topic: "{topic}".
             
             You are now delivering your closing statement for the debate. Your objective is to summarize your strongest points,
             address key opposing arguments, and leave a lasting impression on the audience.
             
             Guidelines:
             1. Briefly recap your strongest arguments
             2. Address the most significant counterarguments
             3. Emphasize why your position should prevail
             4. Be persuasive but honest
             5. End with a compelling conclusion
             
             Consider all previous rounds of debate:
             {all_arguments}
             
             Craft a conclusive closing statement of approximately 250-300 words.
             """),
            ("human", "Please provide your final closing statement for the {stance} position on the topic: {topic}")
        ])
    
    def _format_previous_arguments(self, rounds):
        """Format previous arguments for context."""
        if not rounds:
            return "This is the first round, so there are no previous arguments."
        
        formatted = []
        for i, round_data in enumerate(rounds, 1):
            formatted.append(f"Round {i}:")
            formatted.append(f"Pro argument: {round_data.get('pro_argument', 'N/A')}")
            formatted.append(f"Con argument: {round_data.get('con_argument', 'N/A')}")
        
        return "\n\n".join(formatted)
    
    def generate_argument(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a debate argument based on the current state."""
        
        # Get the current round, defaulting to 0 if not present
        current_round = state.get("current_round", 0)
        
        # Get or initialize rounds list
        rounds = state.get("rounds", [])
        
        # Check if we need to add a new round entry
        if current_round >= len(rounds):
            # If this is a new round, add an empty dict for this round
            rounds = list(rounds) + [{}]
        
        # Get topic and introduction from state
        topic = state.get("topic", "")
        introduction = state.get("introduction", "")
        
        # Get previous arguments for context
        previous_rounds = state["rounds"][:current_round]
        previous_arguments = self._format_previous_arguments(previous_rounds)
        
        # Prepare current round if it doesn't exist
        if current_round >= len(state["rounds"]):
            state["rounds"].append({})
        
        # Generate the argument
        chain = self.argument_prompt | self.llm
        response = chain.invoke({
            "name": self.name,
            "stance": self.stance,
            "topic": self.topic,
            "round_num": current_round + 1,  # 1-indexed for human readability
            "background_info": self.background_info,
            "previous_arguments": previous_arguments
        })
        
        # Update the rounds list with the new argument
        updated_rounds = list(rounds)
        
        # If the current round dict doesn't exist, create it
        if current_round >= len(updated_rounds):
            updated_rounds.append({})
        
        # Make a copy of the current round dict
        current_round_data = dict(updated_rounds[current_round])
        
        # Add the argument based on stance
        arg_key = f"{self.stance}_argument"
        current_round_data[arg_key] = response.content
        
        # Update the round in the list
        updated_rounds[current_round] = current_round_data
        
        return {"rounds": updated_rounds}
    
    def generate_conclusion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a concluding statement for the debate."""
        # Format all arguments from all rounds
        all_arguments = self._format_previous_arguments(state.get("rounds", []))
        
        # Generate conclusion
        chain = self.conclusion_prompt | self.llm
        response = chain.invoke({
            "name": self.name,
            "stance": self.stance,
            "topic": state.get("topic", self.topic),  # Use self.topic as fallback
            "all_arguments": all_arguments
        })
        
        # Create a new dict for state updates
        updates = {}
        
        # Update state with conclusion
        if self.stance == "pro":
            updates["pro_conclusion"] = response.content
        else:
            updates["con_conclusion"] = response.content
        
        return updates
