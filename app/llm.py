from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


llm = ChatOpenAI(
    model="gpt-6-luna",
    temperature=0.5,
    reasoning_effort="none",
)
