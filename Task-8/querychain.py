from langchain_core.messages import HumanMessage, SystemMessage
from openai import OpenAI
from dotenv import load_dotenv
import os
from pyswip import Prolog
load_dotenv()
from pyswip import Prolog
from functions import extract_code
from langchain_openai import ChatOpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
prolog = Prolog()
first_response = "unknown"




question = input("Ask a Question")
model = ChatOpenAI(model = "gpt-4o")
count = 0
while ( first_response.lower() == "unknown" and count < 5):
    messages = [
        SystemMessage( "Answer true if the question I ask is a true or false question, answer false if it a ranking question, and unknown if neither"),
        HumanMessage(question)
    ]

    classifier = model.invoke(messages)
    first_response = classifier.content
    print (first_response)
    if (first_response.lower() == "unknown"):
        messages2 = [
            SystemMessage( "Rewrite the question here: {question}"),
            HumanMessage(question)
        ]
        question = model.invoke(messages2)
        question = question.content
        print (question)
        count += 1
    
if (first_response.lower() == "true"):
    