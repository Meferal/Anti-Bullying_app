import os
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("OPENAI_API_KEY")
print(f"Loaded Key: {key}")
