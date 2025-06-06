import os
from dotenv import load_dotenv

# LangChain OpenAI chat model (correct and up-to-date)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# LangChain prompt templating
from langchain.prompts import PromptTemplate

# LangChain community components (document loading, vector DB)
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS

# Text splitting utility
from langchain.text_splitter import CharacterTextSplitter

# Prolog integration
from pyswip import Prolog

# Your custom helper
from functions import extract_code

# LangGraph components
from langgraph.graph import StateGraph, END

# Typed state structure
from typing import TypedDict, Optional

# nodes for langgraph

class QAState(TypedDict, total=False):
    question: str
    classification: str
    result: str
    reasoning: str
    llm: any  # your ChatOpenAI instance

def classify_question(state):
    llm = state["llm"]
    question = state["question"]
    prompt = PromptTemplate.from_template(
        "Answer 'true' if the question is a yes/no question, 'false' if it is a ranking/constraint puzzle, and 'unknown' otherwise.\n\nQuestion: {question}"
    )
    classification = llm.invoke(prompt.format(question=question)).content.strip().lower()
    print("classifiction: ", classification)

    attempts = 0
    while classification == "unknown" and attempts < 5:
        rewrite_prompt = PromptTemplate.from_template("Rewrite the question to make it more classifiable: {question}")
        question = llm.invoke(rewrite_prompt.format(question=question)).content
        classification = llm.invoke(prompt.format(question=question)).content.strip().lower()
        attempts += 1


    # print("QUESTION:", question)
    # print("CLASSIFIED AS:", classification)
    # print("FULL STATE:", state)


    state["question"] = question
    state["classification"] = classification
    return state

# answers true false question 
def true_branch(state):
    question = state["question"]
    llm = state["llm"]

    print("true branch")

    # LangChain RAG
    loader = TextLoader("animals_kb.pl")
    docs = loader.load()
    
    splitter = CharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    retriever = vectorstore.as_retriever()

    relevant_docs = relevant_docs = retriever.invoke(question)

    facts = "\n".join(doc.page_content for doc in relevant_docs)
    print("RAG-retrieved facts:\n", facts)


    query_prompt = PromptTemplate.from_template(
    "You are a Prolog expert. Given a natural language question and a knowledge base, "
    "output only a single-line Prolog query that directly tests whether the statement in the question is true.\n"
    "Do not restate facts like `fish(nemo)` — test what the user is asking.\n"
    "Only use predicates that exist in the knowledge base.\n"
    "For example, if the question is 'Is Nemo a shark?' but there is no `shark/1` predicate, return something like `shark(nemo).`, even if it will fail.\n"
    "Do not make up new predicate names.\n\n"
    "Question: {question}\n\nKnowledge base:\n{kb}"
    )



    query_raw = llm.invoke(query_prompt.format(question=question, kb=facts)).content
    query = extract_code(query_raw).replace("?-", "").replace(".", "").strip()


    # Self-refinement 
    refine_prompt = PromptTemplate.from_template(
        "Here is a question, a knowledge base, and a proposed Prolog query:\n\n"
        "Question: {question}\nKnowledge base:\n{kb}\n\n"
        "Initial Prolog query: {query}\n\n"
        "Reflect step-by-step: is this the correct Prolog query to answer the question? "
        "If not, suggest a revised version. Output only the revised query as a single line. "
        "If the initial query is already good, return it unchanged."
    )
    refined_query_raw = llm.invoke(
        refine_prompt.format(question=question, kb=facts, query=query)
    ).content
    refined_query = extract_code(refined_query_raw).replace("?-", "").replace(".", "").strip()

    print(f"Refined Prolog query: {refined_query}")

    prolog = Prolog()
    prolog.consult("animals_kb.pl")

    try:
        result = list(prolog.query(query))
        state["result"] = "true" if result else "false"
    except Exception as e:
        state["result"] = f"Prolog error: {e}"

    return state



# ranking quesiton 
def false_branch(state):
    question = state["question"]
    llm = state["llm"]

    reasoning_prompt = PromptTemplate.from_template(
        "You are a helpful assistant that solves logic puzzles or ranking problems. "
        "For the question below, provide a ranked list of the items involved (e.g., largest to smallest) "
        "and explain your reasoning in 2-3 sentences.\n\n"
        "Question: {question}"
    )

    reasoning = llm.invoke(reasoning_prompt.format(question=question)).content

    # Save the entire explanation with the ranked output
    state["result"] = reasoning
    return state


def route(state):
    if state["classification"] == "true":
        return "true_branch"
    elif state["classification"] == "false":
        return "false_branch"
    else:
        return END


def build_graph():
    builder = StateGraph(QAState)
    
    builder.add_node("classify", classify_question)
    builder.add_node("route", route)
    builder.add_node("true_branch", true_branch)
    builder.add_node("false_branch", false_branch)


    builder.set_entry_point("classify")

    
    # builder.add_edge("classify", "true_branch")

    builder.add_conditional_edges("classify", route)


    builder.add_edge("true_branch", END)
    builder.add_edge("false_branch", END)

    return builder.compile()


def main():

    load_dotenv()
    llm = ChatOpenAI(model="gpt-4o")

    prolog = Prolog()

    # input
    
    question = input("Enter your question: ")
    initial_state: QAState = {
        "question": question,
        "llm": llm
    }

    graph = build_graph()


    # debugging
    result = graph.invoke(initial_state)
    print("Final Answer:", result.get("result", "No result"))



if __name__ == "__main__":
    main()