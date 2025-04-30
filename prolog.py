from pyswip import Prolog

prolog = Prolog()
prolog.consult("prologue.pl")

while True:
    checker = False

    query = input("?- ")
    if query.strip().lower() in ["exit", "quit"]:
        break
    try:
        
        results = list(prolog.query(query))
        if not results:
            print("false.")
            continue
        # print(results)

        counter = 0
        
        while counter < len(results) and checker == False:
            if results[counter] == {}:
                print ("true.")
                break
            print(results[counter])
            
            user_input = input()

            if user_input.strip() == ";":
                counter += 1
            else:
                break

    except Exception as e:
        print("Error:", e)
