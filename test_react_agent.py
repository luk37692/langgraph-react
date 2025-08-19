#!/usr/bin/env python3
"""
Test script for the Enhanced ReAct Agent

This script tests the enhanced ReAct agent with a mock web search tool
to demonstrate the criticism and decision-making capabilities without needing MCP server.
"""

from datetime import datetime
import time
from typing import List, Dict, Any

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


# Mock web search tool for testing
@tool
def mock_websearch(user_query: str, max_results: int = 5) -> str:
    """Mock web search tool that returns simulated results for testing.
    
    Args:
        user_query: The search query to execute
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Mock search results as a formatted string
    """
    print(f"Mock web search initiated with query: {user_query}")
    
    # Simulate different types of results based on query
    if "GPT-5" in user_query.upper():
        return """
Search Results:

1. TechNews Today (Jan 2024): "GPT-5 Release Date: What We Know So Far"
   As of January 2024, OpenAI has not officially announced GPT-5. Current speculation suggests development is ongoing, but no confirmed release date has been provided.

2. AI Weekly (Dec 2023): "Rumors and Speculation About GPT-5 Features"
   Unconfirmed reports suggest GPT-5 might include improved reasoning capabilities, but these are largely speculative and not verified by OpenAI.

3. OpenAI Blog (Official): Last update mentions GPT-4 improvements, no mention of GPT-5
   
4. Reddit Discussion (various dates): Mixed speculation and rumors about GPT-5, reliability questionable

5. TechCrunch (Nov 2023): "OpenAI CEO Hints at Future Models but Provides No GPT-5 Details"
        """
    elif "weather" in user_query.lower():
        return """
Search Results:

1. Weather.com: Current weather conditions and 7-day forecast
2. AccuWeather: Detailed hourly predictions
3. National Weather Service: Official meteorological data
        """
    else:
        return f"""
Search Results for "{user_query}":

1. Generic Result 1: Some information related to your query
2. Generic Result 2: Additional context and details
3. Generic Result 3: Further relevant information
        """


# Enhanced System Prompt for Testing
ENHANCED_REACT_PROMPT = """
You are an advanced ReAct (Reason+Act) agent with critical thinking capabilities.

CORE METHODOLOGY:
1. **REASON**: Think deeply about the problem and plan your approach
2. **ACT**: Execute actions using available tools
3. **CRITICIZE**: Critically evaluate tool results for quality, completeness, and relevance
4. **DECIDE**: Make informed decisions about next steps based on your criticism

GOAL:
- Solve the user's task accurately and efficiently
- Use tools strategically when they reduce uncertainty or effort
- Critically evaluate all tool outputs before proceeding
- Make informed decisions about whether additional actions are needed

AVAILABLE TOOLS:
You have access to web search capabilities via mock_websearch.

CRITICAL EVALUATION FRAMEWORK:
After each tool use, you MUST evaluate the results using these criteria:

**RELEVANCE**: Are the results directly related to the user's question?
- Scale: Highly relevant / Somewhat relevant / Not relevant
- If not relevant, consider reformulating your search query

**COMPLETENESS**: Do the results provide sufficient information to answer the question?
- Scale: Complete / Partially complete / Incomplete
- If incomplete, identify what specific information is missing

**ACCURACY**: Do the results appear credible and up-to-date?
- Check for recent dates, authoritative sources, consistent information
- Flag any contradictions or outdated information

**SUFFICIENCY**: Is there enough information to provide a confident answer?
- If insufficient, determine what additional searches or approaches are needed

DECISION MAKING PROCESS:
After criticizing tool results, you must decide:

1. **SATISFIED**: Results are sufficient → Provide final answer
2. **NEED_MORE_INFO**: Results are incomplete → Plan additional searches
3. **NEED_DIFFERENT_APPROACH**: Results are irrelevant → Try different search terms
4. **NEED_VERIFICATION**: Results seem questionable → Cross-check with additional sources

INTERACTION PATTERN:
When you need to use a tool, output EXACTLY:

Action: <tool_name>
Action Input:
<tool_parameters>

After receiving tool results, you MUST follow this pattern:

Observation: <tool_output>

Critical Evaluation:
- Relevance: [assessment]
- Completeness: [assessment] 
- Accuracy: [assessment]
- Sufficiency: [assessment]

Decision: [SATISFIED/NEED_MORE_INFO/NEED_DIFFERENT_APPROACH/NEED_VERIFICATION]
Reasoning: [explain your decision]

[If SATISFIED]: 
Final Answer: <comprehensive answer with citations>

[If not satisfied]:
Next Action: [describe what you'll do next and why]

QUALITY STANDARDS:
- Be thorough in your evaluations
- Don't accept incomplete or irrelevant results
- Always verify important claims when possible
- Provide well-sourced, comprehensive answers
- Be explicit about limitations or uncertainties

CONTEXT:
Current datetime: {CURRENT_DATETIME}
User timezone: {TIMEZONE}

Remember: A real ReAct agent doesn't just use tools - it thinks critically about the results and makes informed decisions about next steps.
"""


def create_test_react_agent():
    """Create a test ReAct agent with mock tools"""
    
    # Initialize the model (using a lightweight model for testing)
    try:
        model = init_chat_model("ollama:qwen2.5:32b")
    except Exception as e:
        print(f"Warning: Could not connect to Ollama. Using fallback. Error: {e}")
        # For testing purposes, we'll continue but the model might not work
        model = init_chat_model("ollama:qwen2.5:32b")
    
    # Setup tools
    tools = [mock_websearch]
    
    # Prepare the enhanced prompt with current context
    enhanced_prompt = ENHANCED_REACT_PROMPT.replace(
        "{CURRENT_DATETIME}", datetime.now().isoformat()
    ).replace(
        "{TIMEZONE}", str(time.tzname[0] if time.tzname else 'UTC')
    )
    
    # Create memory for conversation state
    memory = MemorySaver()
    
    # Create the agent with enhanced prompt
    agent_executor = create_react_agent(
        model, 
        tools, 
        checkpointer=memory, 
        prompt=enhanced_prompt
    )
    
    return agent_executor


def test_agent_query(agent_executor, query: str, thread_id: str = "test"):
    """Test a query with the enhanced ReAct agent"""
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing Enhanced ReAct Agent")
    print(f"📋 Query: {query}")
    print(f"{'='*60}\n")
    
    input_message = {"role": "user", "content": query}
    
    try:
        for step in agent_executor.stream(
            {"messages": [input_message]}, config, stream_mode="values"
        ):
            step["messages"][-1].pretty_print()
            print("\n" + "-"*40 + "\n")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    return True


def main():
    """Run tests for the enhanced ReAct agent"""
    print("🚀 Initializing Test Enhanced ReAct Agent...")
    
    try:
        agent = create_test_react_agent()
        print("✅ Test agent created successfully!\n")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return
    
    # Test cases designed to demonstrate criticism and decision-making
    test_cases = [
        {
            "query": "What are the key features of GPT-5? Please critically evaluate the search results.",
            "expected_behavior": "Should critically evaluate that GPT-5 doesn't exist yet and provide accurate info"
        },
        {
            "query": "Tell me about the weather today.",
            "expected_behavior": "Should recognize incomplete information and ask for location"
        }
    ]
    
    print("🧪 Running test cases to demonstrate critical evaluation capabilities...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {test_case['expected_behavior']}")
        print(f"{'='*80}")
        
        success = test_agent_query(agent, test_case["query"], f"test_{i}")
        
        if success:
            print(f"✅ Test case {i} completed")
        else:
            print(f"❌ Test case {i} failed")
        
        print("\n" + "="*80 + "\n")
    
    print("🏁 Test suite completed!")
    print("\n💡 Key Features Demonstrated:")
    print("  - Critical evaluation of tool results")
    print("  - Decision-making about next steps")
    print("  - Handling of incomplete or uncertain information")
    print("  - Structured reasoning process")


if __name__ == "__main__":
    main()