



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