#!/usr/bin/env python3
"""
Main entry point for the Enhanced ReAct Agent

This script provides a command-line interface to interact with the enhanced ReAct agent
that includes tool result criticism and decision-making capabilities.
"""

import sys
import argparse
from react_agent import create_enhanced_react_agent, run_agent_query


def main():
    parser = argparse.ArgumentParser(description="Enhanced ReAct Agent with Critical Thinking")
    parser.add_argument("query", nargs="?", help="Query to ask the agent")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--thread-id", default="main", help="Thread ID for conversation continuity")
    
    args = parser.parse_args()
    
    # Create the enhanced agent
    print("🚀 Initializing Enhanced ReAct Agent...")
    agent = create_enhanced_react_agent()
    print("✅ Agent ready!\n")
    
    if args.interactive:
        print("🤖 Interactive mode - type 'quit' or 'exit' to stop")
        print("💡 The agent will critically evaluate all tool results before providing answers\n")
        
        while True:
            try:
                query = input("You: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif query:
                    run_agent_query(agent, query, args.thread_id)
                    print("\n")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    else:
        if not args.query:
            print("❌ Please provide a query or use --interactive mode")
            sys.exit(1)
        
        run_agent_query(agent, args.query, args.thread_id)


if __name__ == "__main__":
    main()