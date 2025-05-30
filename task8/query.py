import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pyswip import Prolog
from functions import extract_code  # your custom function


def retrieve_relevant_kb(question, kb_file="animals_kb.pl"):
    terms = question.lower().split()
    with open(kb_file) as f:
        lines = f.readlines()
    return "\n".join([line for line in lines if any(term in line.lower() for term in terms)])


def main():

    load_dotenv()
    llm = ChatOpenAI(model="gpt-4o")

    prolog = Prolog()

    # Step 1: Get input
    question = input("Enter your question: ")
    classification_prompt = PromptTemplate.from_template(
        "Answer 'true' if the question is a yes/no question, 'false' if it is a ranking/constraint puzzle, and 'unknown' otherwise.\n\nQuestion: {question}"
    )
    classification = llm.invoke(classification_prompt.format(question=question)).content.strip().lower()

    # Retry unknown up to 5 times
    counter = 0
    while classification == "unknown" and counter < 5:
        rewriter_prompt = PromptTemplate.from_template("Rewrite the question to make it more classifiable: {question}")
        question = llm.invoke(rewriter_prompt.format(question=question)).content
        classification = llm.invoke(classification_prompt.format(question=question)).content.strip().lower()
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
        facts = llm.invoke(facts_prompt.format(question=question)).content

        # facts = retrieve_relevant_kb(question)

        
        # with open("prologue.pl", "w") as f:
        #     f.write(extract_code(facts))

        prolog.consult("animals_kb.pl")

        # Generate query
        query_prompt = PromptTemplate.from_template(
            "Output only a valid Prolog query (just one line) that can be answered from this knowledge base. Use only the actual predicates like 'fish/1', 'mammal/1', etc., defined in the knowledge base. Do not invent new predicates.\n\nQuestion: {question}\n\nKnowledge base: {kb}"
        )
        query_response = llm.invoke(query_prompt.format(question=question, kb=facts)).content
        query = extract_code(query_response).strip()
        query = query.replace("?-", "").replace(".", "").strip()  # clean up for pyswip


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
        reasoning = llm.invoke(reasoning_prompt.format(question=question)).content
        print(reasoning)

        answer_prompt = PromptTemplate.from_template(
            "From the reasoning below, extract only the correct multiple choice answer (e.g., 'A'):\n\n{reasoning}"
        )
        answer = llm.invoke(answer_prompt.format(reasoning=reasoning)).content.strip()
        print(answer)


if __name__ == "__main__":
    main()