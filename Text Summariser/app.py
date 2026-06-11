from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load API key
load_dotenv()

# Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.3
)

# Read text file
with open("sample.txt", "r", encoding="utf-8") as file:
    text = file.read()

# Prompt
prompt = PromptTemplate.from_template(
    """
    Summarize the following text in short and easy language:

    {text}
    """
)

# Create chain
chain = prompt | llm

# Run chain
response = chain.invoke({"text": text})

# Print summary
print("\n📌 Summary:\n")
print(response.content)