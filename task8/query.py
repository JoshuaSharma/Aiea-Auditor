import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pyswip import Prolog
from functions import extract_code  # your custom function

load_dotenv()
llm = ChatOpenAI(model="gpt-4o")

prolog = Prolog()

# Step 1: Get input
question = input("Enter your question: ")
classification_prompt = PromptTemplate.from_template(
    "Answer 'true' if the question is a yes/no question, 'false' if it is a ranking/constraint puzzle, and 'unknown' otherwise.\n\nQuestion: {question}"
)
classification = llm.predict(classification_prompt.format(question=question)).strip().lower()

# Retry unknown up to 5 times
counter = 0
while classification == "unknown" and counter < 5:
    rewriter_prompt = PromptTemplate.from_template("Rewrite the question to make it more classifiable: {question}")
    question = llm.predict(rewriter_prompt.format(question=question))
    classification = llm.predict(classification_prompt.format(question=question)).strip().lower()
    counter += 1

if classification == "unknown":
    print("Error: Cannot classify question after 5 attempts.")
    exit()

# Step 2: TRUE/FALSE classification
if classification == "true":
    # Generate Prolog facts from the question
    facts_prompt = PromptTemplate.from_template(
        "You are a helpful assistant that outputs raw Prolog code from this question: {question}"
    )
    facts = llm.predict(facts_prompt.format(question=question))
    
    with open("prologue.pl", "w") as f:
        f.write(extract_code(facts))

    prolog.consult("animals_kb.pl")

    # Generate query
    query_prompt = PromptTemplate.from_template(
        "Write a Prolog query (only the query line) to answer this question: {question} based on this knowledge base: {kb}"
    )
    query = llm.predict(query_prompt.format(question=question, kb=facts)).strip()

    print(f"Generated Prolog query: {query}")


    try:
        result = list(prolog.query(query))
        print("true" if result else "false.")
    except Exception as e:
        print("Prolog error:", e)

# Step 3: RANKING/CONSTRAINT classification
elif classification == "false":
    reasoning_prompt = PromptTemplate.from_template(
        "You are a helpful assistant that solves logic puzzles using constraint logic reasoning. "
        "For this ranking problem, output the reasoning and answer as a Python dictionary:\n\n{question}"
    )
    reasoning = llm.predict(reasoning_prompt.format(question=question))
    print(reasoning)

    answer_prompt = PromptTemplate.from_template(
        "From the reasoning below, extract only the correct multiple choice answer (e.g., 'A'):\n\n{reasoning}"
    )
    answer = llm.predict(answer_prompt.format(reasoning=reasoning)).strip()
    print(answer)
