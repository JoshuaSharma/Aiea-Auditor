import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pyswip import Prolog
from functions import extract_code  # your custom function
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

# manuel RAG
def retrieve_relevant_kb(question, kb_file="animals_kb.pl"):

    # Break the question into lowercase terms
    terms = question.lower().split()

    # Read the knowledge base file
    with open(kb_file, "r") as file:
        kb_lines = file.readlines()

    # Collect lines that contain any of the terms
    relevant_lines = []
    for line in kb_lines:
        line_lower = line.lower()
        if any(term in line_lower for term in terms):
            relevant_lines.append(line)

    # Return the matching lines as a single string
    return "\n".join(relevant_lines)

# langchain RAG
def retrieve_relevant_context_with_rag(question, kb_file="animals_kb.pl"):


    # Load and split KB
    loader = TextLoader(kb_file)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

    # Embed and store in FAISS
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    retriever = vectorstore.as_retriever()

    # Get relevant context
    relevant_docs = retriever.get_relevant_documents(question)
    return "\n".join(doc.page_content for doc in relevant_docs)




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

        # this doesn't use the facts in database but asking for Chatgpt directly without context
        # an good example is ask something that's not true in general but true 
        # according to knowledge base to test out
        # facts = llm.invoke(facts_prompt.format(question=question)).content

        # this will make sure chatgpt use the knowledge base 
        # manuel RAG
        # facts = retrieve_relevant_kb(question)

        # langchain RAG
        facts = retrieve_relevant_context_with_rag(question)


        
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