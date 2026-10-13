import chromadb
import pymupdf4llm
from langchain_text_splitters import MarkdownTextSplitter

books = ['book1', 'book2']

splitter = MarkdownTextSplitter(chunk_size = 1000, chunk_overlap = 100)

texts = []
metadatas = []
ids = []



for n in books:
    pages = pymupdf4llm.to_markdown(f'../books/{n}.pdf', page_chunks = True, )
    print(n, "pages:", len(pages))

    for page in pages:
        page_num = page['metadata']['page_number']
        chunks = splitter.split_text(page["text"])
        for i, chunk in enumerate(chunks):
            if len(chunk.strip())<100:
                continue
            texts.append(chunk)
            metadatas.append({"book":n,"page":page_num})
            ids.append(f"{n}-p{page_num}-c{i}")

print(len(texts), len(metadatas), len(ids))
print(metadatas[0])
print(texts[0][:200])





client = chromadb.PersistentClient(path="chromadb")
collection = client.get_or_create_collection(name="medical_books")

for start in range(0,len(texts),500):
    end = start + 500
    collection.add(
        documents=texts[start:end],
        metadatas=metadatas[start:end],
        ids=ids[start:end],
    )
    print("Added up to", end)

print("Stored:", collection.count())