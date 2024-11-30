# DOGE Hackathon - RAG - Document Search with Chat

This project is a Retrieval-Augmented Generation (RAG) system that allows users to upload documents, store them in a vector database, and query them using a conversational AI assistant powered by OpenAI's GPT-4 and GROK model.

## Features

- Upload PDF, Excel, Docx, or Txt files.
- Store and index document content in a vector database using FAISS.
- Ask questions related to the uploaded documents and get precise, step-by-step answers.
- Supports embedding generation using OpenAI's GPT-4 model.
- User-friendly interface built with Streamlit.

## Installation

### Prerequisites

1. Python 3.10 or higher
2. Pip or a compatible package manager
3. An OpenAI API Key

### Setup Instructions

1. Clone the repository:

   
   ```git clone https://github.com/your-repo-name/doge-hackathon-rag.git```
   ```cd doge-hackathon-rag```
   
2. Create a virtual environment:

   ```python -m venv venv```
   ```source venv/bin/activate```  # For Linux/Mac
   ```venv\Scripts\activate```     # For Windows
  
3. Install dependencies:
  ```pip install -r requirements.txt```

4. Set up the .env file:
   Create a .env file in the root directory with the following variables:
   ```OPENAI_API_KEY=your-openai-api-key```
   ```VECTOR_DB_PATH_DB=vectorstore```
   ```GROK_API_KEY=your-grok-api-key```

### Usage

1.Start the Streamlit application:

  ```streamlit run app.py```
  
2.Upload your documents via the sidebar interface:

  Supported formats: .pdf, .xlsx, .docx, .txt.
  Provide a name and a brief description of the document.

3.Ask questions in the chat interface on the right side of the screen.




