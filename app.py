import streamlit as st
import os
from dotenv import load_dotenv
from helper import FileHandler, ChatHandler

# Load environment variables
load_dotenv()

# Initialize Handlers
VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH_DB', 'vectordb')
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

file_handler = FileHandler(VECTOR_DB_PATH)
chat_handler = ChatHandler(VECTOR_DB_PATH)

# Streamlit UI
st.set_page_config(layout="wide", page_title="DOGE Hackathon")
st.title("DOGE Hackathon - RAG - Document Search with Chat")

# Left Side: File Upload
st.sidebar.header("Upload Documents")
uploaded_file = st.sidebar.file_uploader("Upload PDF, Excel, Docx, or Txt", type=["pdf", "xlsx", "docx", "txt"])
document_name = st.sidebar.text_input("Document Name", "")
document_description = st.sidebar.text_area("Document Description", "")

if st.sidebar.button("Process File"):
    if uploaded_file:
        with st.spinner("Processing your file..."):
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
model_choice = st.selectbox("Select Model", ["OpenAI", "Grok"])

if st.button("Submit Question"):
    if user_question:
        with st.spinner("Processing your question..."):
            response = chat_handler.answer_question(user_question, model_choice)
        st.write(response)
    else:
        st.warning("Please enter a question.")
