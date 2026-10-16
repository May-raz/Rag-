import chromadb
from groq import Groq

groq_client = Groq()

chroma_client = chromadb.PersistentClient(path="chromadb")

collection = chroma_client.get_collection("medical_books")

MAX_DISTANCE = 0.95
SYSTEM_PROMPT =""" You are medical assistant who answers questions from the knwoledge of these books. 
You can only use the context provided to you to answer the question, do not use context from your own knowledge.
You have 2 textbooks from which you get 5 excrepts with the most relevance from which you use to answer the questions asked from you.
Some of the excrepts may be not be related to the answer at all, ignore them. 
If the answer to the question is not given in the excrepts then let the person know that the question is out of the scope of the books.  
Cite pages in the same format as [book1, p. 178].
Keep Answers short and clear.
Remind User to consult a doctor.
always use '[]' brackets."""

def ask(question):
    results = collection.query(query_texts=[question], n_results=5)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]


    if distances[0] > MAX_DISTANCE:
        answer = {"answer":"No info was found about your question in the books!","sources":[]}
        return answer

    parts = []
    for document, metadata in zip(documents, metadatas):
        block = f'[{metadata["book"]}, p. { metadata["page"]}]\n{document}'
        parts.append(block)
    context = "\n\n".join(parts)
    user_message = f"Context: \n{context} \n\n Question: \n {question}"
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role":"system","content":SYSTEM_PROMPT},
                  {"role":"user", "content":user_message}],
        temperature=0.2
    )
    answer_text = response.choices[0].message.content
    return {"answer":answer_text, "sources":metadatas}

if __name__ == "__main__":
    X = ask(input("Type your Question here: "))
    print(X["answer"])
    print(X["sources"])
    X = ask("best pizza in Rome")
    print(X["answer"])
    print(X["sources"])