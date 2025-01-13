from typing import Annotated

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from langchain_ollama import OllamaLLM

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

llm = OllamaLLM(model="llama3.2:1b", base_url="http://localhost:11434")

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()


try:
    image = graph.get_graph().draw_mermaid_png()

    with open("diagram.png", "wb") as image_file:
        image_file.write(image)
except Exception as e:
    print(f"Error {e} occurred")

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1])

while True:
    try:
        user_input = input("User: ")

        if user_input.lower() in ["quit", "q"]:
            print("Goodbye")
            break
        
        stream_graph_updates(user_input)
    except Exception as e:
        print(f"Error {e} occurred")
        break
