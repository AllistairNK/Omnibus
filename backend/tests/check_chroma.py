import chromadb

client = chromadb.HttpClient(host="localhost", port=8001)

collections = client.list_collections()
print('Collections:', [c.name for c in collections])

for col in collections:
    c = client.get_collection(col.name)
    print(f'\n--- {col.name} ---')
    print('Count:', c.count())
    
    all_data = c.get(include=['metadatas', 'documents'])
    for i, doc_id in enumerate(all_data['ids']):
        print(f'  [{i}] id={doc_id}')
        print(f'       filename={all_data["metadatas"][i].get("filename")}')
        print(f'       document_id={all_data["metadatas"][i].get("document_id")}')
        print(f'       chunk_index={all_data["metadatas"][i].get("chunk_index")}')
        print(f'       created_at={all_data["metadatas"][i].get("created_at")}')
        print(f'       preview={all_data["documents"][i][:80]}...')