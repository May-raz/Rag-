import chromadb
from groq import Groq

groq_client = Groq()

chroma_client = chromadb.PersistentClient(path="chromadb")

collection = chroma_client.get_collection("medical_books")

MAX_DISTANCE = 0.95

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
    return context

if __name__ == "__main__":
    print(ask("What are the symptoms of meningioma?"))
    print(ask("best pizza in Rome"))