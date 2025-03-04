from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

class ScorekeeperAgent:
    """Agent that evaluates debate arguments and determines a winner."""
    
    def __init__(self, llm):
        self.llm = llm
        
        # Updated prompt to use formatted_debate instead of individual components
        self.evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an impartial debate judge with expertise in critical thinking, logical reasoning, and argument analysis.
             Your task is to evaluate a debate on the topic: "{topic}" and determine a winner based on the quality of arguments presented.
             
             Evaluation criteria:
             1. Logical reasoning and argument structure (30 points)
             2. Use of evidence and factual accuracy (30 points)
             3. Addressing counterarguments (20 points)
             4. Persuasiveness and clarity (20 points)
             
             For each side (Pro and Con), assign a score out of 100 points based on these criteria.
             
             Debate content:
             {formatted_debate}
             
             Provide a detailed evaluation of both sides' arguments, noting strengths and weaknesses.
             Then provide numerical scores for each side and declare a winner (or a tie if the scores are within 5 points of each other).
             """),
            ("human", "Please evaluate the debate and determine the winner.")
        ])
    
    def _format_rounds_summary(self, rounds):
        """Format all debate rounds into a readable summary."""
        formatted = []
        for i, round_data in enumerate(rounds, 1):
            formatted.append(f"Round {i}:")
            formatted.append(f"Pro argument: {round_data.get('pro_argument', 'N/A')}")
            if 'pro_fact_check' in round_data:
                formatted.append(f"Pro fact check: {round_data.get('pro_fact_check', 'N/A')}")
            
            formatted.append(f"Con argument: {round_data.get('con_argument', 'N/A')}")
            if 'con_fact_check' in round_data:
                formatted.append(f"Con fact check: {round_data.get('con_fact_check', 'N/A')}")
            
            formatted.append("")  # Empty line between rounds
        
        return "\n".join(formatted)
    
    def _format_debate_content(self, topic: str, rounds_data: list, pro_conclusion: str, con_conclusion: str) -> str:
        """Format the entire debate content for evaluation."""
        # Format the debate rounds
        rounds_summary = self._format_rounds_summary(rounds_data)
        
        # Put everything together
        formatted_debate = f"""
        Topic: {topic}
        
        ROUNDS:
        {rounds_summary}
        
        CONCLUSIONS:
        Pro conclusion: {pro_conclusion}
        
        Con conclusion: {con_conclusion}
        """
        
        return formatted_debate
    
    def _parse_evaluation(self, evaluation: str) -> tuple:
        """Extract scores and winner from the evaluation text."""
        # Default values
        pro_score = 0
        con_score = 0
        winner = "Tie"
        
        # Simple parsing logic - this could be made more robust
        try:
            # Look for score patterns like "Pro score: 85" or "Pro: 85 points"
            import re
            
            pro_pattern = r'pro[\s\w]*:?\s*(\d+)[\s\w]*points?'
            con_pattern = r'con[\s\w]*:?\s*(\d+)[\s\w]*points?'
            
            pro_match = re.search(pro_pattern, evaluation.lower())
            con_match = re.search(con_pattern, evaluation.lower())
            
            if pro_match:
                pro_score = int(pro_match.group(1))
            
            if con_match:
                con_score = int(con_match.group(1))
            
            # Determine winner
            if abs(pro_score - con_score) <= 5:
                winner = "Tie"
            elif pro_score > con_score:
                winner = "Pro"
            else:
                winner = "Con"
        
        except Exception:
            # If parsing fails, use default values
            pass
        
        return pro_score, con_score, winner

    def evaluate_debate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the debate and determine the winner."""
        
        # Use get() to safely access state keys
        topic = state.get("topic", "Unknown topic")
        introduction = state.get("introduction", "")
        pro_conclusion = state.get("pro_conclusion", "")
        con_conclusion = state.get("con_conclusion", "")
        rounds_data = state.get("rounds", [])
        
        # Format all debate content for evaluation
        formatted_debate = self._format_debate_content(topic, rounds_data, pro_conclusion, con_conclusion)
        
        # Generate evaluation using the formatted debate content
        chain = self.evaluation_prompt | self.llm
        response = chain.invoke({
            "topic": topic,
            "formatted_debate": formatted_debate
        })
        
        # Parse evaluation and scores
        evaluation = response.content
        pro_score, con_score, winner = self._parse_evaluation(evaluation)
        
        # Return updates to the state
        return {
            "evaluation": evaluation,
            "pro_score": pro_score,
            "con_score": con_score,
            "winner": winner
        }
