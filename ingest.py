"""
ingest.py - Build the FAISS index from the Azure VM Markdown docs.

Run (venv activated):  python ingest.py
Output: faiss_index/index.faiss + faiss_index/index.pkl
"""
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEV_MODE = True                      # True = only the 14 *troubleshoot* files
DATA_DIR = Path("data/virtual-machines")
INDEX_DIR = Path("faiss_index")
CHUNK_SIZE = 1000                    # max characters per chunk
CHUNK_OVERLAP = 150                  # characters shared between 2 chunks
BATCH_SIZE = 64                      # chunks sent per embedding call
PAUSE_SECONDS = 1.0                  # pause between batches (rate limit)
MAX_RETRIES = 5
DOCS_BASE_URL = "https://learn.microsoft.com/en-us/azure/virtual-machines/"

# YAML front matter at the top of each MS Learn file:  ---\ntitle: ...\n---
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TITLE_RE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# 1. Load the .md files
# ---------------------------------------------------------------------------
def load_documents():
    pattern = "**/*troubleshoot*.md" if DEV_MODE else "**/*.md"
    loader = DirectoryLoader(
        str(DATA_DIR),
        glob=pattern,
        loader_cls=TextLoader,
        # utf-8-sig = utf-8 that also removes a BOM if the file has one
        loader_kwargs={"encoding": "utf-8-sig"},
    )
    return loader.load()   # list of Document(page_content=..., metadata={"source": path})


# ---------------------------------------------------------------------------
# 2. Clean each document + build useful metadata for citations
# ---------------------------------------------------------------------------
def clean_document(doc):
    text = doc.page_content
    title = None

    match = FRONTMATTER_RE.match(text)
    if match:
        title_match = TITLE_RE.search(match.group(1))
        if title_match:
            title = title_match.group(1).strip().strip("'\"")
        text = text[match.end():]          # remove the front matter from the text

    # Path relative to data/virtual-machines, with "/" even on Windows
    full_path = Path(doc.metadata["source"]).resolve()
    rel_path = full_path.relative_to(DATA_DIR.resolve()).as_posix()

    doc.page_content = text.strip()
    doc.metadata = {
        "source": rel_path,
        "title": title or rel_path,
        # Approximate public URL (OK for most articles, not for includes/)
        "url": DOCS_BASE_URL + rel_path.removesuffix(".md"),
    }
    return doc


# ---------------------------------------------------------------------------
# 3. Embed in batches (with retry) and build the FAISS index
# ---------------------------------------------------------------------------
def build_index(chunks, embeddings):
    vectorstore = None
    total = len(chunks)

    for start in range(0, total, BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        for attempt in range(MAX_RETRIES):
            try:
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(batch, embeddings)
                else:
                    vectorstore.add_documents(batch)
                break                                  # success -> leave retry loop
            except Exception as error:                 # e.g. 429 rate limit
                wait = 5 * 2 ** attempt                # 5, 10, 20, 40, 80 s
                print(f"  Batch {start}: {error} -> retry in {wait}s")
                time.sleep(wait)
        else:
            # runs only if the for loop never hit "break"
            raise RuntimeError(f"Batch {start} failed after {MAX_RETRIES} attempts")

        print(f"  {min(start + BATCH_SIZE, total)}/{total} chunks embedded")
        time.sleep(PAUSE_SECONDS)

    return vectorstore


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    load_dotenv()                                     # reads .env into os.environ
    if not os.getenv("MISTRAL_API_KEY"):
        raise SystemExit("MISTRAL_API_KEY is missing in .env")

    print(f"DEV_MODE={DEV_MODE}")
    docs = load_documents()
    print(f"{len(docs)} files loaded")

    docs = [clean_document(d) for d in docs]
    docs = [d for d in docs if d.page_content]        # drop empty files

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,                   # split on ## headings first
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,                         # position of chunk in file
    )
    chunks = splitter.split_documents(docs)

    total_chars = sum(len(c.page_content) for c in chunks)
    print(f"{len(chunks)} chunks, avg {total_chars // max(len(chunks), 1)} chars")
    print(f"~{total_chars // 4:,} tokens to embed (rough estimate)")

    embeddings = MistralAIEmbeddings(model="mistral-embed")
    vectorstore = build_index(chunks, embeddings)

    vectorstore.save_local(str(INDEX_DIR))
    print(f"Index saved to {INDEX_DIR}/")

    # Quick sanity check: does retrieval return relevant files?
    question = "Creating a restore point fails, how can I fix it?"
    print(f"\nTest query: {question}")
    for doc in vectorstore.similarity_search(question, k=3):
        print(f"  - {doc.metadata['title']}  ({doc.metadata['source']})")


if __name__ == "__main__":   # = run main() only when executed directly, not imported
    main()
