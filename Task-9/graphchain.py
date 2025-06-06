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
    generate_facts = [
        SystemMessage(content="You are a helpful assistant that only responds with raw Prolog code (no comments), including dynamic rules."),
        HumanMessage(content=f"Translate the facts in this query into valid Prolog using these:\n{context}\nQuestion: {state['question']}")
    ]
    prolog_code_raw = model.invoke(generate_facts).content
    state["prolog_code"] = extract_code(prolog_code_raw)

    with open("prologue.pl", "w") as file:
        file.write(state["prolog_code"])

    try:
        prolog.consult("prologue.pl")
    except Exception as e:
        state["result"] = f"Error consulting Prolog file: {e}"
        return state
    print("query")
    generate_query = [
        SystemMessage(content="Only return a valid Prolog query (e.g. `color(sky, blue).`). No `?-`, no explanation."),
        HumanMessage(content=f"Write a query that would answer the question: {state['question']}.\nProlog code: {state['prolog_code']}")
    ]
    raw_query = model.invoke(generate_query).content.strip()
    state["query"] = extract_code(raw_query)



    try:
        result = list(prolog.query(state["query"]))
        state["result"] = "true" if result else "false"
    except Exception as e:
        state["result"] = f"Error executing Prolog query: {e}"

    return state

'''def translate_to_prolog(state: State) -> State:
    relevant_docs = retriever.get_relevant_documents(state["question"])
    context = "\n".join([doc.page_content for doc in relevant_docs])
    state["context"] = context

    generate_facts = [
        SystemMessage(content="You are a helpful assistant that only responds with raw Prolog code (no comments), including dynamic rules."),
        HumanMessage(content=f"Translate the facts in this query into valid Prolog using these:\n{context}\nQuestion: {state['question']}")
    ]
    prolog_code_raw = model.invoke(generate_facts).content
    state["prolog_code"] = extract_code(prolog_code_raw)

    with open("prologue.pl", "w") as file:
        file.write(state["prolog_code"])
    try:
        prolog.consult("prologue.pl")
    except:
        state["result"] = "Error running prolog"
        return state
    
    questionquery = [
        SystemMessage(content="Only return a valid Prolog query (e.g. `color(sky, blue).`). No `?-`, no explanation."),
        HumanMessage(content=f"Write a query that would answer the question {question} given this prolog file file {prolog_code}.")
    ]
    raw_query = model.invoke(generate_query).content.strip()
    state["query"] = extract_code(raw_query)

    try:
        result = list(prolog.query(state["query"]))
        state["result"] = "true" if result else "false"
    except:
        state["result"] = "query error"
    return state'''

def solve_ranking(state: State) -> State:
    context = state.get("context", "")
    reasoning = model.invoke([
        SystemMessage(content="You are a helpful assistant that solves ranking puzzles using constraint logic reasoning."),
        HumanMessage(content=state["question"])
    ]).content.strip()

    answer = model.invoke([
        SystemMessage(content=f"From the reasoning below, output only the correct multiple choice answer (e.g., 'A') and consider this {context}:"),
        HumanMessage(content=reasoning)
    ]).content.strip()

    state["result"] = f"{reasoning}\n{answer}"
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
builder.add_node("ranking", solve_ranking)
builder.set_entry_point("classify")
builder.add_conditional_edges("classify", route)
builder.add_edge("rewrite", "classify")
builder.add_edge("translate", END)
builder.add_edge("ranking", END)

app = builder.compile()

if __name__ == "__main__":
    q = input("Ask a question: ")
    result = app.invoke({"question": q})
    print(result.get("result", result.get("error", "No result")))
