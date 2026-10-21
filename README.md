# Medical RAG (experimental)

Ask questions in plain English and get answers taken **only** from two medical
textbooks, with page citations like `[book2, p. 422]`.

This is an experimental project. The same code works for **any** collection of
documents. See [Using it for other data](#using-it-for-other-data).

---

## What RAG means here

**RAG = Retrieval-Augmented Generation.**

A normal chatbot answers from memory. It can't tell you where an answer came
from, and it can make things up. This project works differently:

1. **Retrieval:** find the passages in *our* books that are closest to the question.
2. **Generation:** give those passages to an LLM along with strict rules, so it writes
   an answer **from those passages only** and cites the pages.

The facts come from the books. The LLM only reads them and writes the answer.

---

## Project layout

```
medical-rag/
├── books/                 # Source PDFs (book1.pdf, book2.pdf), not in git
├── backend/
│   ├── ingest.py          # One-time: PDFs → chunks → vector database
│   ├── query_test.py      # Retrieval check only (no LLM)
│   ├── groq_test.py       # LLM connection check only (no books)
│   ├── rag.py             # The real thing: ask(question) → answer + sources
│   ├── requirements.txt   # Python packages
│   ├── chromadb/          # The vector database (created by ingest.py, not in git)
│   └── venv/              # Python virtual environment (not in git)
├── app/                   # Front end (planned: Streamlit)
├── .env                   # GROQ_API_KEY (not in git)
└── .gitignore
```

---

## How it works, step by step

### 1. Ingestion: `ingest.py` (run once)

```
PDF ──► pages as Markdown ──► chunks of ~1000 chars ──► Chroma (stores text + embedding)
```

- `pymupdf4llm.to_markdown(..., page_chunks=True)` reads each PDF **page by page**,
  so every piece of text knows its page number.
- `MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)` cuts each page into
  chunks of about 1000 characters. The 100-character overlap means a sentence
  near a cut appears in both chunks.
- Chunks shorter than 100 characters are skipped (headers, page numbers, noise).
- Each chunk is stored with:
  - **metadata** `{"book": "book1", "page": 178}`, which is later used for citations
  - an **ID** like `book1-p178-c0` (book, page, chunk number)
- `collection.add(...)` stores them in batches of 500. At this moment Chroma turns every
  chunk into an **embedding**: 384 numbers that represent its meaning. Texts with
  similar meanings get similar numbers.
- Result: **5,009 chunks** in the collection `medical_books`.

### 2. Answering a question: `rag.py` → `ask(question)`

```
question
   │
   ▼
Chroma: embed the question, return the 5 closest chunks + distances
   │
   ├── best distance > MAX_DISTANCE?  ──► return "No info was found..."  (LLM never called)
   │
   ▼
Label each chunk "[book1, p. 178]" and join them into one context string
   │
   ▼
Groq LLM: SYSTEM_PROMPT (rules) + "Context: ... Question: ..."
   │
   ▼
return {"answer": "...text with citations...", "sources": [{"book":..., "page":...}, ...]}
```

Details:

| Piece | What it does | Why |
|---|---|---|
| `collection.query(query_texts=[question], n_results=5)` | Embeds the question with the **same model** used at ingestion and finds the 5 nearest chunks | Same model, so question and chunks are comparable |
| `results["documents"][0]` etc. | `[0]` = results for our first (only) question | Chroma can take many questions at once, so results are nested lists |
| `MAX_DISTANCE = 0.95` | If even the best chunk is farther than this, the question is rejected | Chroma **always** returns 5 results, even for "best pizza in Rome". The cutoff stops unrelated questions, saves LLM tokens, and stops the LLM answering from memory |
| Labelled context | `[book2, p. 422]\n<chunk text>` blocks joined with blank lines | The LLM can only cite what it sees, so the label travels with the text |
| `SYSTEM_PROMPT` | The rules: use only the excerpts, ignore unrelated ones, say when the answer isn't there, cite as `[book, p. N]`, be brief, suggest a doctor | For a medical app, an invented answer is dangerous |
| `temperature=0.2` | Low randomness | Keeps answers close to the text |
| `response.choices[0].message.content` | The answer text only | The response also contains IDs, token usage and the model's hidden reasoning |
| Return dict | Same shape for answered **and** rejected questions | The front end can always read `result["answer"]` and `result["sources"]` |

`if __name__ == "__main__":` holds test code that runs only when you run
`python rag.py` directly, not when another file (such as the front end) imports `ask`.

### Measured distances (for calibrating the cutoff)

| Question | Best distance | Result |
|---|---|---|
| What are the symptoms of meningioma? | 0.62 (5 results: 0.62–0.81) | Answered |
| best pizza in Rome | 1.58 | Rejected |

A cost of roughly **1,500 tokens and ~1.3 s per answered question** was measured on `openai/gpt-oss-120b`.

---

## Setup and running

All commands are for **PowerShell** and are run **from `backend/`**. The database path
`chromadb` is relative, so running from anywhere else breaks it.

```powershell
cd D:\work\medical-rag\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Groq key (only for this window). Never paste keys into code or chat.
$env:GROQ_API_KEY = "your-key-here"
[bool]$env:GROQ_API_KEY        # True = set (doesn't prove it's valid)

# One time only, if chromadb/ doesn't exist yet:
python ingest.py

# Ask questions:
python rag.py
```

> **Re-ingesting:** delete `backend/chromadb/` first. Otherwise `add()` hits
> duplicate IDs.

LLM provider: **Groq**, model `openai/gpt-oss-120b` (fallback: `openai/gpt-oss-20b`).

---

## Using it for other data

The pipeline doesn't know anything about medicine. Only these parts are specific to the books:

### 1. Swap the documents (`ingest.py`)

- Put your PDFs in `books/` (or any folder) and change the list:
  ```python
  books = ['book1', 'book2']          # file names without .pdf
  ```
  and the path `f'../books/{n}.pdf'` if you use another folder.
- **Not PDFs?** Only the "read the file" line changes. Whatever you use, end up
  with a list of text pieces plus a page or section number for each. For example:
  - `.txt` / `.md`: read the file and split on headings or blank lines
  - Word: `python-docx`
  - Web pages: fetch + `BeautifulSoup`
  - CSV / database rows: one row (or group of rows) = one chunk

### 2. Change the metadata (citations)

Metadata is what appears in citations and sources. Use whatever makes sense:

```python
{"book": n, "page": page_num}              # current
{"file": "policy.pdf", "section": "4.2"}   # e.g. company documents
{"url": "...", "title": "..."}             # e.g. web pages
```

If you change the keys, also update the label line in `rag.py`:
`f'[{metadata["book"]}, p. {metadata["page"]}]\n{document}'`.

### 3. Tune the chunking

| Setting | Current | Effect of raising it | Effect of lowering it |
|---|---|---|---|
| `chunk_size` | 1000 | More context per chunk, but less precise matches | Sharper matches, but each chunk carries less context |
| `chunk_overlap` | 100 | Fewer ideas cut in half, more duplicate text | Less duplication |
| Minimum length | 100 | Drops more noise (and maybe short useful lines) | Keeps more fragments |

### 4. Use a new collection name

```python
client.get_or_create_collection(name="medical_books")   # ingest.py
chroma_client.get_collection("medical_books")           # rag.py
```

Use a new name per dataset (e.g. `"company_docs"`) so datasets don't mix.

### 5. Re-calibrate `MAX_DISTANCE`

The cutoff depends on the data and the embedding model, so **don't reuse 0.95 blindly**:

1. Run `query_test.py` with 3–4 questions you know are answered in the data, and
   note the best distance for each.
2. Do the same with 2–3 clearly unrelated questions.
3. Pick a value **with a safety margin** above the relevant ones and well below the
   unrelated ones. A value right at the edge (e.g. 0.82 when the best match was
   0.81) would reject slightly differently worded valid questions.

### 6. Rewrite `SYSTEM_PROMPT`

Change the role ("medical assistant using two textbooks" → "HR assistant using the
employee handbook") and any domain-specific rules (the "consult a doctor" line).
Keep the core rules for any dataset:

- answer **only** from the excerpts
- ignore unrelated excerpts
- say clearly when the answer isn't there
- cite with the exact label format, e.g. "use plain square brackets `[ ]`"

### 7. (Optional) Change the models

- **Embedding model:** Chroma's default (`all-MiniLM-L6-v2`, 384 numbers, English).
  For other languages or better quality, pass a different `embedding_function` to the
  collection. You must then **re-ingest** and **re-calibrate `MAX_DISTANCE`**, because
  distances from different models aren't comparable.
- **LLM:** change `model="openai/gpt-oss-120b"` in `rag.py`. List the models your Groq
  key can use with `groq_client.models.list()` (see `groq_test.py`).

---

## Known issues / limitations

- **Chunks can end mid-sentence:** each page is split on its own, so a sentence that
  continues onto the next page is cut.
- **Noise pages are stored:** table of contents, contributor lists and index pages.
- **Ligature gaps** from PDF extraction, e.g. `signifi cant`.
- **Sources list isn't filtered:** it lists all 5 retrieved chunks (including
  duplicates and ones the answer didn't use).
- **Citation format can vary:** the model sometimes writes `【book2, p. 422】`
  instead of `[book2, p. 422]`. A rule asking for `[]` brackets was added to
  `SYSTEM_PROMPT`; check that it holds over more test questions.
- **Overgeneralizing:** a fact from a small study or a rare subtype may be presented
  as general. The prompt could ask the model to say when that's the case.
- **The API key isn't loaded from `.env` yet.** It has to be set in the shell
  (planned: `python-dotenv`).
- `ingest.py` prints "Added up to 5500" at the end. This is cosmetic.

---

## Status and next steps

- [x] Ingestion (5,009 chunks)
- [x] Retrieval + distance cutoff
- [x] `ask()` returns an LLM answer with citations and sources
- [ ] Test 3–4 more questions (vague, out-of-scope, reworded), adjust `MAX_DISTANCE` / prompt
- [ ] Load `GROQ_API_KEY` from `.env` with `python-dotenv`
- [ ] Streamlit front end that imports `ask()` from `rag.py`
- [ ] Share it with ngrok (public URL → local Streamlit)

### Front end plan: Streamlit + ngrok

```
Phone / other PC ──► https://xxxx.ngrok-free.app ──► ngrok tunnel ──► your PC: streamlit (port 8501) ──► ask() ──► Chroma + Groq
```

- **Streamlit** turns a Python script into a web page (text box, button, answer).
  It runs in the same Python as `rag.py`, so it can simply `from rag import ask`.
  This replaces the earlier FastAPI + Expo plan: no separate API or phone app needed.
- **ngrok** gives your local Streamlit a temporary public URL. It is a **tunnel, not
  hosting**: the app only works while your PC, Streamlit and ngrok are all running.
  The free URL changes each time you restart ngrok.
- Run Streamlit **from `backend/`** (same relative-path rule as `rag.py`):
  `streamlit run app.py`, then in a second window `ngrok http 8501`.
- Anyone with the URL can use the app, and every question costs your Groq tokens.
  Stop ngrok when you're not demoing.
