from openai import OpenAI
from dotenv import load_dotenv
import os
from pyswip import Prolog
load_dotenv()
from pyswip import Prolog
from functions import extract_code

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
prolog = Prolog()
first_response = "unknown"
question = input()
counter = 0 
while (first_response.lower() == "unknown" and counter != 5):
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Answer true if the question I ask is a true or false question, answer false if it a ranking question, and unknown if neither"},
        {"role": "user", "content": question}]
    )

    first_response = response.choices[0].message.content
    if (first_response.lower() == "unknown"):
        response2 = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Rewrite the question"},
            {"role": "user", "content": question}]
        )
        question = response2.choices[0].message.content
        counter += 1

    #print(first_response)

if counter == 5:
    print ("Error: Cannot classify question")
else:
    if first_response.lower() == "true":
        response2 = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a helpful assistant that only responds with raw prolog code, including dynamic rules."},
            {"role": "user", "content": f"Can you translate the facts of this query response into prolog: {question}."}]
            )
        prolog_content = response2.choices[0].message.content
        #print(prolog_content)
        with open("prologue.pl", "w") as file:
            #file.write(prolog_content[9:-4])
            file.write(extract_code(prolog_content))


        prolog.consult("prologue.pl")
        response3 = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a helpful assistant that only responds with raw prolog code, including dynamic rules."},
            {"role": "user", "content": f"Write a query that would answer the question {question} given this prolog file file {prolog_content}."}]
            )
        query = response3.choices[0].message.content
        

        

        result = list(prolog.query(query))
        if len(result) == 0:
                print("true.")  # Empty result means the statement is true
        else:
                print("false.")
        #print(result)

        
    
    else:
        #Constraint Optimization
        pass

'''response2 = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "system", "content": "You are a helpful assistant that only responds with raw prolog code, including dynamic rules."},
    {"role": "user", "content": f"Can you translate this response into prolog: {first_response}."}]
)
prolog_content = response2.choices[0].message.content'''

