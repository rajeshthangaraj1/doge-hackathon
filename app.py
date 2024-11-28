import streamlit as st
import os
from dotenv import load_dotenv
from helper import FileHandler, ChatHandler
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

# Initialize Handlers
VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH_DB', 'vectorstore')
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

file_handler = FileHandler(VECTOR_DB_PATH)
chat_handler = ChatHandler(VECTOR_DB_PATH)

# Streamlit UI
st.set_page_config(layout="wide", page_title="DOGE Hackathon")
st.title("DOGE Hackathon - Document Search with Chat")

# Left Side: File Upload
st.sidebar.header("Upload Documents")
uploaded_file = st.sidebar.file_uploader("Upload PDF, Excel, Docx, or Txt", type=["pdf", "xlsx", "docx", "txt"])
document_name = st.sidebar.text_input("Document Name", "Untitled Document")
document_description = st.sidebar.text_area("Document Description", "Provide a brief description of the document.")

if st.sidebar.button("Process File"):
    if uploaded_file:
        response = file_handler.handle_file_upload(
            file=uploaded_file,
            document_name=document_name,
            document_description=document_description,
        )
        st.sidebar.success(f"File processed: {response['message']}")
    else:
        st.sidebar.warning("Please upload a file before processing.")

# Right Side: Chat Interface
st.header("Ask Questions")
user_question = st.text_input("Type your question here:")
if st.button("Submit Question"):
    if user_question:
        response = chat_handler.answer_question(user_question)
        st.write(response)
    else:
        st.warning("Please enter a question.")
