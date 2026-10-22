"""
rag.py - Answer a question with the FAISS index + Mistral (RAG).

Run (venv activated):  python rag.py "your question"
Needs: faiss_index/ built by ingest.py, MISTRAL_API_KEY in .env
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
INDEX_DIR = Path("faiss_index")
EMBED_MODEL = "mistral-embed"        # must be the same model as in ingest.py
CHAT_MODEL = "mistral-small-latest"
TOP_K = 4                            # number of chunks given to the LLM
MAX_DISTANCE = None                  # drop chunks farther than this (None = keep all)
TEMPERATURE = 0.0                    # 0 = stable answers, no creativity
NO_ANSWER = "I don't know, the documentation I have does not cover this."

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an Azure Virtual Machines support assistant.\n"
     "Answer ONLY with the information in the context below.\n"
     "If the context does not contain the answer, say exactly: "
     f"\"{NO_ANSWER}\"\n"
     "Be concise and practical (steps, commands). "
     "Cite the sources you use with their number, like [1] or [2].\n\n"
     "Context:\n{context}"),
    ("human", "{question}"),
])


# ---------------------------------------------------------------------------
# 1. Load the index (once) and build the chain (once)
# ---------------------------------------------------------------------------
_vectorstore = None
_chain = None


def get_components():
    """Create the vector store and the LLM chain on first call, then reuse them."""
    global _vectorstore, _chain
    if _chain is None:
        load_dotenv()
        if not os.getenv("MISTRAL_API_KEY"):
            raise SystemExit("MISTRAL_API_KEY is missing in .env")
        if not INDEX_DIR.exists():
            raise SystemExit(f"{INDEX_DIR}/ not found: run python ingest.py first")

        embeddings = MistralAIEmbeddings(model=EMBED_MODEL)
        _vectorstore = FAISS.load_local(
            str(INDEX_DIR),
            embeddings,
            # index.pkl is a pickle file: only OK because we created it ourselves
            allow_dangerous_deserialization=True,
        )

        llm = ChatMistralAI(model=CHAT_MODEL, temperature=TEMPERATURE)
        # LCEL: the "|" pipes the output of one step into the next
        _chain = PROMPT | llm | StrOutputParser()
    return _vectorstore, _chain


# ---------------------------------------------------------------------------
# 2. Helpers: search the chunks, format them for the prompt, list unique sources
# ---------------------------------------------------------------------------
def search(vectorstore, question):
    """Top-k chunks with their distance to the question (lower = closer)."""
    return vectorstore.similarity_search_with_score(question, k=TOP_K)


def retrieve(vectorstore, question):
    """Top-k chunks, without the ones farther than MAX_DISTANCE."""
    return [doc for doc, distance in search(vectorstore, question)
            if MAX_DISTANCE is None or distance <= MAX_DISTANCE]


def format_context(docs):
    parts = []
    for i, doc in enumerate(docs, start=1):
        header = f"[{i}] {doc.metadata['title']} ({doc.metadata['source']})"
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def unique_sources(docs):
    """One entry per file, in retrieval order (several chunks can share a file)."""
    seen = set()
    sources = []
    for doc in docs:
        path = doc.metadata["source"]
        if path not in seen:
            seen.add(path)
            sources.append({
                "title": doc.metadata["title"],
                "source": path,
                "url": doc.metadata["url"],
            })
    return sources


# ---------------------------------------------------------------------------
# 3. Main function: question -> answer + sources (reused by the API in step 9)
# ---------------------------------------------------------------------------
def ask(question):
    vectorstore, chain = get_components()
    docs = retrieve(vectorstore, question)           # top-k chunks from FAISS
    if not docs:                                     # nothing close enough: skip the LLM call
        return {"answer": NO_ANSWER, "sources": []}
    answer = chain.invoke({
        "context": format_context(docs),
        "question": question,
    })
    # No sources when the model says the docs don't cover the question
    if answer.strip().startswith("I don't know"):
        return {"answer": answer, "sources": []}
    return {"answer": answer, "sources": unique_sources(docs)}


if __name__ == "__main__":
    # sys.argv = command-line arguments, like process.argv in Node
    question = " ".join(sys.argv[1:]) or "Creating a restore point fails, how can I fix it?"
    print(f"Question: {question}\n")

    result = ask(question)
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  - {s['title']}  ({s['source']})")
