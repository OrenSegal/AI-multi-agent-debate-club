import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import OPENROUTER_MODEL

class FactChecker:
    """Checks the factual accuracy of debate arguments."""
    
    def __init__(self, model_name: str = OPENROUTER_MODEL):
        # Initialize LLM
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model_name=model_name
        )
        
        # Define fact checking prompt
        self.fact_check_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an impartial fact-checker with expertise in verifying claims made in debates.
             
             Your task is to review the following argument and identify any factual claims that:
             1. Are demonstrably false
             2. Are misleading or lack important context
             3. Misrepresent scientific consensus
             4. Contain logical fallacies
             
             Focus only on factual accuracy, not the quality of the argument or its persuasiveness.
             Be specific about which claims are problematic and why.
             If a claim is accurate but missing important context, provide that context.
             If a claim is false, provide the correct information.
             If unsure about a claim, indicate your uncertainty rather than making a definitive judgment.
             
             Argument to check:
             {argument}
             """),
            ("human", "Please fact-check this argument and provide your assessment.")
        ])
    
    def check_facts(self, argument: str) -> str:
        """Check an argument for factual accuracy."""
        try:
            chain = self.fact_check_prompt | self.llm
            response = chain.invoke({
                "argument": argument
            })
            return response.content
        except Exception as e:
            # If fact-checking fails for any reason, return a message
            return f"Error in fact checking: {str(e)}"

    def check_fallacies(self, text: str) -> Dict[str, Any]:
        """Identify logical fallacies in the provided text."""
        fallacies = {
            "ad_hominem": False,
            "straw_man": False,
            "false_dichotomy": False,
            "appeal_to_authority": False,
            "slippery_slope": False,
            "circular_reasoning": False,
            "hasty_generalization": False
        }
        
        try:
            # Use the LLM to identify logical fallacies
            prompt = f"""Analyze the following debate argument for logical fallacies. 
            For each of the following fallacy types, respond only with "Yes" if present or "No" if not present:
            
            1. Ad hominem
            2. Straw man
            3. False dichotomy
            4. Appeal to authority
            5. Slippery slope
            6. Circular reasoning
            7. Hasty generalization
            
            Argument:
            {text}
            """
            
            response = self.llm.invoke(prompt)
            
            # Parse the response to update fallacies dictionary
            lines = response.content.strip().split("\n")
            fallacy_types = list(fallacies.keys())
            
            for i, line in enumerate(lines):
                if i < len(fallacy_types) and "yes" in line.lower():
                    fallacies[fallacy_types[i]] = True
            
            return fallacies
            
        except Exception as e:
            print(f"Error in fallacy detection: {e}")
            return fallacies
