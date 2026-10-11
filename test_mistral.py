from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings

load_dotenv()  # reads .env and puts MISTRAL_API_KEY in the environment variables

# Test 1: the chat model answers
llm = ChatMistralAI(model="mistral-small-latest")
print(llm.invoke("Reply only 'OK' if you receive me.").content)

# Test 2: embeddings work (one text -> one vector of numbers)
emb = MistralAIEmbeddings(model="mistral-embed")
vector = emb.embed_query("My VM does not respond to RDP")
print(f"Vector dimension: {len(vector)}")