import chromadb

client = chromadb.PersistentClient(path='./chroma_data')
collections = client.list_collections()
print('Collections:', collections)

for col in collections:
    c = client.get_collection(col.name)
    print(f'\n--- {col.name} ---')
    print('Count:', c.count())
    print('Peek:', c.peek())