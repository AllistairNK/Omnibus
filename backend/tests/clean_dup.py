# tests/cleanup_duplicate.py
import chromadb

client = chromadb.PersistentClient(path='./chroma_data')
col = client.get_collection("user_d1335931-8ee7-46e4-a348-adae08b0e542_documents")

# Delete the duplicate (the later upload)
col.delete(ids=["80c11aaf-f085-4aa0-b6c1-6b1beab748d6_0"])
print("Deleted duplicate. Count:", col.count())