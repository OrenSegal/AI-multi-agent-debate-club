from langchain_core.prompts import ChatPromptTemplate

class DebateSetter:
    """Agent that sets up the debate and introduces the topic."""
    
    def __init__(self, llm, topic: str, background_info: str):
        self.llm = llm
        self.topic = topic
        self.background_info = background_info
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional debate moderator. Your role is to introduce a debate topic clearly and neutrally.
             Provide a balanced introduction that:
             1. Explains the topic
             2. Provides context and background information
             3. Explains why this topic is important
             4. Outlines the key points of contention
             
             Do NOT take any stance on the issue. Remain completely neutral. Your introduction should be concise but informative,
             around 250-350 words. End with "Let the debate begin."
             """),
            ("human", "Please introduce the debate topic: {topic}. Here is some background information that may help: {background_info}")
        ])
    
    def set_debate(self, state):
        """Set up the debate and provide an introduction."""
        # Create the introduction
        chain = self.prompt | self.llm
        response = chain.invoke({
            "topic": self.topic,
            "background_info": self.background_info
        })
        
        # Update the state with the introduction
        state["introduction"] = response.content
        
        return state
