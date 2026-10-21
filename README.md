# Medical RAG

A small project where you can ask questions about two medical books and get answers **only from those books**, with the page number where the answer was found.

This was my first RAG project. I built it to learn how RAG works.

---

## What is RAG?

RAG stands for **Retrieval-Augmented Generation**. In simple words:

1. **Retrieval:** find the parts of the books that match the question.
2. **Generation:** give those parts to an AI model and ask it to write an answer using **only** them.

A normal chatbot answers from its memory and can make things up. Here the answer comes from the books, and every answer shows which page it came from, like `[book2, p. 422]`.

---

## How it works

```
PDF books
   ↓  ingest.py (run once)
Small pieces of text (chunks) saved in a database (Chroma)
   ↓
User asks a question
   ↓  rag.py
Find the 5 closest chunks
   ↓
Too far from the question? → "No info was found"
   ↓
Send the chunks + question to the AI (Groq)
   ↓
Answer with page numbers
```

---

## Files

| File | What it does |
|---|---|
| `backend/ingest.py` | Reads both PDFs, cuts every page into small chunks (about 1000 characters) and saves them in the Chroma database. I only run this once. |
| `backend/query_test.py` | Tests the search alone: prints the 5 closest chunks for a question. |
| `backend/groq_test.py` | Tests the connection to the Groq AI alone. |
| `backend/rag.py` | The main part. The `ask(question)` function finds the chunks, sends them to the AI and returns the answer and the sources. |
| `backend/app.py` | A simple web page made with Streamlit, where you type a question. |
| `backend/api.py` | A small API made with FastAPI, so other apps (like a phone app) can send questions. |
| `backend/requirements.txt` | The Python packages needed. |

Not uploaded to GitHub: the PDF books, the database (`chromadb/`), `venv/` and `.env` (my API key).

---

## Tools I used

- **Python**
- **Chroma**: the database that stores the chunks and finds the closest ones
- **pymupdf4llm**: reads the PDFs
- **Groq**: runs the AI model (`openai/gpt-oss-120b`)
- **Streamlit**: the web page
- **FastAPI + Uvicorn**: the API
- **ngrok**: to open the app on my phone

---

## How to run it

All commands are run from inside the `backend` folder.

**1. Set up**
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**2. Add your Groq API key** (get one free from console.groq.com)
```
$env:GROQ_API_KEY = "your-key-here"
```

**3. Put the books in place and build the database (only once)**

Put the PDFs in a `books` folder next to `backend`, named `book1.pdf` and `book2.pdf`, then run:
```
python ingest.py
```

**4. Ask questions**

In the terminal:
```
python rag.py
```

On a web page:
```
streamlit run app.py
```

As an API (test it at http://localhost:8000/docs):
```
uvicorn api:app --reload --port 8000
```

---

## Some important parts

- **Distance cutoff (`MAX_DISTANCE = 1.2`):** the database always gives back 5 results, even if the question has nothing to do with medicine. Every result has a "distance" (smaller means a better match). If even the best one is too far, the app says "No info was found" and doesn't call the AI at all.
  - "What are the symptoms of meningioma?" gave a best distance of 0.62, so it was answered.
  - "best pizza in Rome" gave 1.58, so it was rejected.
- **System prompt:** rules for the AI: only use the given text, ignore the parts that don't match, say so if the answer isn't there, cite pages like `[book1, p. 178]`, keep it short and tell the user to see a doctor.
- **Temperature 0.2:** makes the AI less creative, so it sticks to the book text.

---

## Using it with other documents

The code isn't only for medical books. To use other files:

1. Put your own PDFs in the `books` folder and change the names in `ingest.py`.
2. Give the collection a new name (in both `ingest.py` and `rag.py`) so the data doesn't mix.
3. Change the system prompt in `rag.py` (for example "You are an assistant for this company handbook").
4. Test a few questions with `query_test.py` and change `MAX_DISTANCE` if good questions get rejected.

---

## What I learned

- How embeddings work: text is turned into numbers, and similar meanings end up close together.
- Why a RAG app needs a cutoff, and how to choose it by testing.
- Testing each part on its own (search first, then the AI) makes it easier to find bugs.
- Lists, dicts and objects in Python, and when to use `[ ]`, `{ }` and `.`
- Writing functions that **return** data instead of printing it.
- Never putting API keys in code or on GitHub.
- Building a web page with Streamlit and an API with FastAPI.

---

## Problems I know about

- Some chunks stop in the middle of a sentence, because each page is cut separately.
- Some useless pages were also saved (table of contents, index).
- Some words have gaps from the PDF, like `signifi cant`.
- The sources list can show the same page twice.

---

## Next steps

- Test more questions
- Load the API key from the `.env` file
- Finish the phone app (Expo)
