import streamlit as st
import os
from dotenv import load_dotenv
from helper import FileHandler, ChatHandler

# Load environment variables
load_dotenv()

# Initialize Handlers
VECTOR_DB_PATH = st.secrets["VECTOR_DB_PATH_DB"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GROK_API_KEY = st.secrets["GROK_API_KEY"]
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

file_handler = FileHandler(VECTOR_DB_PATH,OPENAI_API_KEY,GROK_API_KEY)
chat_handler = ChatHandler(VECTOR_DB_PATH,OPENAI_API_KEY,GROK_API_KEY)

# Streamlit UI
st.set_page_config(layout="wide", page_title="DOGE Hackathon - Reducing Government Waste Effectively")
st.title("DOGE Hackathon - Energy Efficiency in Government")
# Enable the below line to show the sidebar

# Left Side: File Upload
# st.sidebar.header("Upload Documents")
# uploaded_file = st.sidebar.file_uploader("Upload PDF, Excel, Docx, or Txt", type=["pdf", "xlsx", "docx", "txt", "csv"])
# document_name = st.sidebar.text_input("Document Name", "")
# document_description = st.sidebar.text_area("Document Description", "")

# if st.sidebar.button("Process File"):
#     if uploaded_file:
#         with st.spinner("Processing your file..."):
#             response = file_handler.handle_file_upload(
#                 file=uploaded_file,
#                 document_name=document_name,
#                 document_description=document_description,
#             )
#             st.sidebar.success(f"File processed: {response['message']}")
#     else:
#         st.sidebar.warning("Please upload a file before processing.")

# Right Side: Chat Interface
st.header("Ask Questions")
user_question = st.text_input("Type your question here:")

if st.button("Submit Question"):
    if user_question:
        with st.spinner("Processing your question..."):
            response = chat_handler.answer_question(user_question)
        st.write(response)
    else:
        st.warning("Please enter a question.")
