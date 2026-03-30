from dotenv import load_dotenv
load_dotenv()
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), timeout=10.0)
resp = client.embeddings.create(model='text-embedding-3-small', input=['test'])
print('SUCCESS:', len(resp.data[0].embedding), 'dimensions')