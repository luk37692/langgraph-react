"""
Enhanced ReAct Agent with Tool Result Criticism and Decision Making

This module implements a real ReAct (Reason+Act) agent that:
1. Reasons about the problem and plans actions
2. Acts by using available tools
3. Criticizes tool results for completeness, relevance, and accuracy
4. Decides on next steps based on critical evaluation
"""

import asyncio
import traceback
from datetime import datetime
import time
from typing import List, Dict, Any

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from mcp import ClientSession
from mcp.client.sse import sse_client


# Enhanced System Prompt for Real ReAct Agent with Criticism
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
You have access to web search capabilities via websearch_sse_mcp_client.

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


async def _websearch_mcp_async(user_query: str, fetch_results: bool = True, max_results: int = 5) -> str:
    """Internal async function for web search via MCP"""
    try:
        async with sse_client("http://localhost:8005/mcp") as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected to SSE MCP server")

                # Initialize the MCP session
                print("\n=== Initializing MCP Session ===")
                init_result = await session.initialize()
                print(f"Initialization: {init_result}")

                if fetch_results:
                    print("\n=== Fetching Web Search Results ===")
                    
                    # Use the correct MCP method to call the tool
                    tool_result = await session.call_tool(
                        name="search_web",
                        arguments={
                            "user_input": user_query,
                            "fetch_content": True,
                            "max_results": max_results
                        }
                    )
                    
                    print(f"Tool call result: {tool_result}")
                    
                    # Extract the actual results from the tool response
                    if tool_result.content:
                        results = []
                        for content_item in tool_result.content:
                            if hasattr(content_item, 'text'):
                                print(f"Search results: {content_item.text}")
                                results.append(content_item.text)
                            else:
                                print(f"Result: {content_item}")
                                results.append(str(content_item))
                        return "\n".join(results)
                    else:
                        print("No results found")
                        return "No results found"

    except Exception as e:
        print(f"❌ SSE MCP connection failed: {e}")
        print(f"Full error details:")
        traceback.print_exc()
        return f"Error: {str(e)}"


@tool
def websearch_sse_mcp_client(user_query: str, max_results: int = 5) -> str:
    """Search the web for information using MCP server.
    
    Args:
        user_query: The search query to execute
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Search results as a formatted string
    """
    print(f"Web search initiated with query: {user_query}")
    
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_websearch_mcp_async(user_query, True, max_results))
            return result
        finally:
            loop.close()
    except Exception as e:
        return f"Error executing web search: {str(e)}"


def create_enhanced_react_agent():
    """Create an enhanced ReAct agent with criticism and decision-making capabilities"""
    
    # Initialize the model
    model = init_chat_model("ollama:qwen2.5:32b")
    
    # Setup tools
    tools = [websearch_sse_mcp_client]
    
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


def run_agent_query(agent_executor, query: str, thread_id: str = "enhanced_react"):
    """Run a query through the enhanced ReAct agent"""
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"\n{'='*60}")
    print(f"🤖 Enhanced ReAct Agent Query: {query}")
    print(f"{'='*60}\n")
    
    input_message = {"role": "user", "content": query}
    
    for step in agent_executor.stream(
        {"messages": [input_message]}, config, stream_mode="values"
    ):
        step["messages"][-1].pretty_print()
        print("\n" + "-"*40 + "\n")


if __name__ == "__main__":
    # Example usage
    agent = create_enhanced_react_agent()
    
    # Test with a query that requires critical evaluation
    test_query = (
        "What are the key features of GPT-5? Please make sure to critically evaluate "
        "the search results and determine if the information is accurate and up-to-date."
    )
    
    run_agent_query(agent, test_query)