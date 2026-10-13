import chromadb

client = chromadb.PersistentClient(path="chromadb")

collection = client.get_collection("medical_books")

results = collection.query(query_texts=["best pizza in Rome"], n_results=5)

documents = results["documents"][0]
metadatas = results["metadatas"][0]
distances = results["distances"][0]

for document, metadata, distance in zip(documents, metadatas, distances):
    print(document, metadata, distance)