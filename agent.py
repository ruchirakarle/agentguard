"""The AI agent: talks to a local Ollama model and uses tools through the guard."""
import os

import ollama

from tools import guarded_call, read_file, run_python

MODEL = os.getenv("AGENTGUARD_MODEL", "llama3.2")
MAX_STEPS = 5

SYSTEM_PROMPT = """You are a helpful assistant with two tools:
- read_file: read a file from the workspace folder
- run_python: run Python code in a sandbox (use print() to show results)
Use a tool when it helps answer the user. Keep answers short."""

# These functions are passed to Ollama so the model knows the tool names and inputs.
TOOLS = [run_python, read_file]


def run_agent(user_message: str, verbose: bool = True) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    for _ in range(MAX_STEPS):
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        messages.append(response.message)

        if not response.message.tool_calls:
            return response.message.content

        for call in response.message.tool_calls:
            name = call.function.name
            args = dict(call.function.arguments or {})
            if verbose:
                print(f"  [agent wants]  {name}({args})")
            # Every tool call goes through the guard, even unknown tool names.
            result = guarded_call(name, args)
            if verbose:
                print(f"  [guard result] {result['status']}")
            messages.append({"role": "tool", "content": result["output"], "tool_name": name})

    return "Stopped: the agent took too many steps."


if __name__ == "__main__":
    print(f"AgentGuard agent using model '{MODEL}'. Type 'quit' to exit.")
    print("Try: 'What is 123 * 456? Use Python.'  or  'Summarize suspicious_email.txt'")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue
        try:
            print("Agent:", run_agent(question))
        except Exception as e:
            print(f"Error: {e}")
            print("Is Ollama running? Did you run 'ollama pull " + MODEL + "'?")
