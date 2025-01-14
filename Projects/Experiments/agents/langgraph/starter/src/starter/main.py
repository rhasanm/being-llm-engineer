import getpass
import os
from typing import Annotated
import traceback

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from langchain_ollama import OllamaLLM, ChatOllama
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools.tavily_search import TavilySearchResults

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("TAVILY_API_KEY")

tool = TavilySearchResults(max_results=2)
tools = [tool]

llm = OllamaLLM(model="llama3.2:1b", base_url="http://localhost:11434")
llm = ChatOllama(model="llama3.2:1b", base_url="http://localhost:11434")
llm = ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434")
llm = ChatOllama(model="mistral", base_url="http://localhost:11434")
llm = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

try:
    image = graph.get_graph().draw_mermaid_png()

    with open("diagram.png", "wb") as image_file:
        image_file.write(image)
except Exception as e:
    print(f"Error {e} occurred")

config: RunnableConfig = {"configurable": {"thread_id": "1"}}
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}, config=config, stream_mode="values"):
        event["messages"][-1].pretty_print()

while True:
    try:
        user_input = input("User: ")

        if user_input.lower() in ["quit", "q"]:
            print("Goodbye")
            break
        
        stream_graph_updates(user_input)
    except Exception as e:
        print(f"Error {e} occurred")
        traceback.print_exc()
        break
