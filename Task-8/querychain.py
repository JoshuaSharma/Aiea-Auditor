from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
from pyswip import Prolog
from functions import extract_code
import os

load_dotenv()

#os.environ["LANGSMITH_TRACING"] = "true"
#os.environ["LANGSMITH_API_KEY"] = getpass.getpass()
model = ChatOpenAI(model="gpt-4o")
prolog = Prolog()


loader = TextLoader("rag.txt")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

embedding = OpenAIEmbeddings()
db = FAISS.from_documents(splits, embedding)
retriever = db.as_retriever()


question = input("Ask a question: ")
first_response = "unknown"
counter = 0

while first_response.lower() == "unknown" and counter != 5:
    messages = [
        SystemMessage(content="Answer true if the question I ask is a true or false question, answer false if it a ranking question, and unknown if neither"),
        HumanMessage(content=question)
    ]
    response = model.invoke(messages)
    first_response = response.content.strip()

    if first_response.lower() == "unknown":
        rewrite_messages = [
            SystemMessage(content="Rewrite the question"),
            HumanMessage(content=question)
        ]
        rewritten = model.invoke(rewrite_messages)
        question = rewritten.content.strip()
        counter += 1

if counter == 5:
    print("Error: Cannot classify question")
else:
    if first_response.lower() == "true":
        relevant_docs = retriever.get_relevant_documents(question)
        context = "\n".join([doc.page_content for doc in relevant_docs])

        generate_facts = [
            SystemMessage(content="You are a helpful assistant that only responds with raw prolog code, including dynamic rules."),
            HumanMessage(content=f"Can you translate the facts of this query response into prolog with this: {question}, considering the following Prolog facts:\n{context}")
        ]
        prolog_code = model.invoke(generate_facts).content
        with open("prologue.pl", "w") as file:
            file.write(extract_code(prolog_code))

        prolog.consult("prologue.pl")

        generate_query = [
            SystemMessage(content="You are a helpful assistant that only responds with raw prolog code, including dynamic rules."),
            HumanMessage(content=f"Write a query that would answer the question {question} given this prolog file file {prolog_code}.")
        ]
        query = model.invoke(generate_query).content.strip()
        query= query[13:-4]
        prolog_code = prolog_code[13:-4]

        print (":",query)
        print (":",prolog_code)

        try:
            result = list(prolog.query(query))
            print("true" if result else "false.")
        except Exception as e:
            print("Error executing Prolog query:", e)

    else:
        ranking_reasoning = [
            SystemMessage(content="You are a helpful assistant that solves ranking puzzles using constraint logic reasoning. "
                                  "Output the ranking logic constraints and final assignments as Python dictionaries or structured text."),
            HumanMessage(content=f"Solve this constraint ranking problem and state which option is correct: {question}")
        ]
        reasoning = model.invoke(ranking_reasoning).content.strip()
        print(reasoning)

        extract_answer = [
            SystemMessage(content="From the reasoning below, output only the correct multiple choice answer (e.g., 'A'):"),
            HumanMessage(content=reasoning)
        ]
        answer = model.invoke(extract_answer).content.strip()
        print(answer)