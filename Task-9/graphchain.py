from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from pyswip import Prolog
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from typing import Dict, Any
from functions import extract_code
import os

load_dotenv()

model = ChatOpenAI(model="gpt-4o")
prolog = Prolog()

loader = TextLoader("rag.txt")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
embedding = OpenAIEmbeddings()
db = FAISS.from_documents(splits, embedding)
retriever = db.as_retriever()

class State(TypedDict):
    question: str
    type: str
    attempts: int
    error: str
    context: str
    prolog_code: str
    query: str
    result: str

def classify_question(state: State) -> State:
    question = state["question"]
    messages = [
        SystemMessage(content="Answer true if the question I ask is a true or false question, answer false if it a ranking question, and unknown if neither"),
        HumanMessage(content=question)
    ]
    result = model.invoke(messages).content.strip().lower()
    state["type"] = result
    state["attempts"] = state.get("attempts", 0) + 1
    return state

def rewrite_question(state: State) -> State:
    if state["type"] != "unknown" or state["attempts"] >= 5:
        if state["attempts"] >= 5:
            state["error"] = "Error: Cannot classify question"
        return state
    messages = [
        SystemMessage(content="Rewrite the question"),
        HumanMessage(content=state["question"])
    ]
    rewritten = model.invoke(messages).content.strip()
    state["question"] = rewritten
    return state

def translate_to_prolog(state: State) -> State:
    print("start")
    relevant_docs = retriever.get_relevant_documents(state["question"])
    context = "\n".join([doc.page_content for doc in relevant_docs])
    state["context"] = context
    print("facts")

    def generate_prolog_code(prompt_modifier=""):
        messages = [
            SystemMessage(content=f"""
You are an expert Prolog fact generator. Only write the **minimum** set of facts and rules necessary to determine the truth of a question like: "{state['question']}". 
Do not include unrelated facts like `animal(dog).` unless they directly support the claim.
Use only predicates that are relevant to answering the question. Do not explain.
Output only valid Prolog code.
{prompt_modifier}
"""),
            HumanMessage(content=f"Context:\n{context}")
        ]
        return extract_code(model.invoke(messages).content)

    def generate_query_code(prompt_modifier=""):
        messages = [
            SystemMessage(content=f"""
Generate a **single Prolog query** that answers the question: "{state['question']}" using the facts provided. 
It must return true if the statement is true and false otherwise. 
Return only valid Prolog, no `?-`, no explanation, no punctuation. 
{prompt_modifier}
"""),
            HumanMessage(content=f"Use these facts:\n{state['prolog_code']}")
        ]
        return extract_code(model.invoke(messages).content.strip())

    state["prolog_code"] = generate_prolog_code()
    with open("prologue.pl", "w") as file:
        file.write(state["prolog_code"])

    try:
        prolog.consult("prologue.pl")
    except Exception as e:
        state["result"] = f"Error consulting Prolog file: {e}"
        return state

    print("query")
    state["query"] = generate_query_code()

    try:
        result = list(prolog.query(state["query"]))
        state["result"] = "true" if result else "false"
    except Exception as e:
        print("Self-refinement triggered")
        state["prolog_code"] = generate_prolog_code("Be stricter. Only define what is needed to answer the question.")
        with open("prologue.pl", "w") as file:
            file.write(state["prolog_code"])
        try:
            prolog.consult("prologue.pl")
        except Exception as e2:
            state["result"] = f"Error after retry: {e2}"
            return state

        state["query"] = generate_query_code("Be precise. Make sure the query expresses the full claim.")
        try:
            result = list(prolog.query(state["query"]))
            state["result"] = "true" if result else "false"
        except Exception as e3:
            state["result"] = f"Refined query failed: {e3}"

    return state


def judge_context(state: State) -> State:
    judgment = model.invoke([
        SystemMessage(content="Is the following context relevant to answering the given question? Respond only with 'yes' or 'no'."),
        HumanMessage(content=f"Question:\n{state['question']}\n\nContext:\n{state['context']}")
    ]).content.strip().lower()

    if "no" in judgment:
        state["error"] = "Irrelevant context detected. Cannot proceed with translation."
    return state

def solve_ranking(state: State) -> State:
    context = state.get("context", "")
    reasoning = model.invoke([
        SystemMessage(content="Solve this ranking question step-by-step using reasoning."),
        HumanMessage(content=f"Question:\n{state['question']}\n\nContext:\n{context}")
    ]).content.strip()

    answer = model.invoke([
        SystemMessage(content="Only output the final answer to the question, like 'A', 'B', etc. Do not explain."),
        HumanMessage(content=reasoning)
    ]).content.strip()

    state["result"] = f"{reasoning}\nAnswer: {answer}"
    return state

def route(state: State):
    if state.get("error"):
        return END
    if state["type"] == "unknown":
        return "rewrite"
    elif state["type"] == "true":
        return "translate"
    else:
        return "ranking"

builder = StateGraph(State)
builder.add_node("classify", classify_question)
builder.add_node("rewrite", rewrite_question)
builder.add_node("translate", translate_to_prolog)
builder.add_node("judge_context", judge_context)
builder.add_node("ranking", solve_ranking)
builder.set_entry_point("classify")
builder.add_conditional_edges("classify", route)
builder.add_edge("rewrite", "classify")
builder.add_edge("translate", "judge_context")
builder.add_edge("judge_context", END)
builder.add_edge("ranking", END)

app = builder.compile()

if __name__ == "__main__":
    q = input("Ask a question: ")
    result = app.invoke({"question": q})
    print(result.get("result", result.get("error", "No result")))
