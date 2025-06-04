from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from pyswip import Prolog
import os
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from functions import extract_code

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


def classifyquestion(state: dict):
    question = state["question"]
    msgs = [
        SystemMessage(content="Answer 'true' if the question is true/false, 'ranking' if it's a ranking question, or 'unknown' otherwise."),
        HumanMessage(content=question)
    ]
    result = model.invoke(msgs).content.strip().lower()
    state["type"] = result
    state["attempts"] = state.get("attempts",0) + 1
def rewrite(state:dict):
    question = state["question"]

    qtype = state["type"]

    if (qtype == "unknown"):
        return state
    else if state["attempts"] >= 5:
        state["error"] = "Could not classify after 5 tries"
        return state
        messages = [
            SystemMessage(content="Rewrite the question")
            HumanMessage(content=question)
        ]
        rewritten = model.invoke(msgs).content.strip().lower()
def translate(state:dict):
    relevant_docs = retriever.get_relevant_documents(state["question"])
    context = "\n".join([doc.page_content for doc in relevant_docs])
    



