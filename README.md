# DOGE Hackathon - Energy Efficiency in Government

This project is a Retrieval-Augmented Generation (RAG) system that allows users to query embedded datasets related to government energy consumption. The system is preloaded with energy datasets in a vector database and provides a conversational AI assistant powered by the GROK model.

## Features

- Preloaded vector database with embedded energy datasets.
- Query energy datasets using a conversational AI assistant.
- Supports embedding generation using OpenAI's GPT-4 model.
- User-friendly interface built with Streamlit.

## Updates

- **File Upload Sidebar:** The file upload functionality is currently hidden as the vector database already contains preloaded energy datasets. 
- **Re-enable Sidebar:** If needed, uncomment the sidebar code in `app.py` to allow file uploads. Instructions for enabling this feature are provided in the `Usage` section.


## Installation

### Prerequisites

1. **Python 3.10** or higher
2. **Pip** or a compatible package manager
3. An **OpenAI API Key** and **GROK API Key**

### Setup Instructions

1. **Clone the repository:**

   
   ```bash
    git clone https://github.com/your-repo-name/doge-hackathon-rag.git
    cd doge-hackathon-rag
    ```
   
2. **Create a virtual environment:**

   ```bash
    python -m venv venv
    ```

    - **For Linux/Mac:**

        ```bash
        source venv/bin/activate
        ```

    - **For Windows:**

        ```bash
        venv\Scripts\activate
        ```
  
3. **Install dependencies:**
   ```bash
    pip install -r requirements.txt
    ```

4. **Set up the `.streamlit/secrets.toml` file:**
   Create a secrets.toml file inside the .streamlit folder in the root directory with the following variables:

    ```env
    OPENAI_API_KEY = "your-openai-api-key-here"
    VECTOR_DB_PATH_DB = "./vectordb"
    GROK_API_KEY = "your-grok-api-key-here"

### Usage

1. **Start the Streamlit application:**

   ```bash
    streamlit run app.py
    ```
3. **Re-enable Sidebar (Optional):**
- If you need to upload new documents, enable the sidebar by uncommenting the related code in `app.py`.
- Instructions:
  1. Locate the following lines in `app.py`:
     ```
     # st.sidebar.header("Upload Documents")
     # uploaded_file = st.sidebar.file_uploader("Upload PDF, Excel, Docx, or Txt", type=["pdf", "xlsx", "docx", "txt", "csv"])
     # document_name = st.sidebar.text_input("Document Name", "")
     # document_description = st.sidebar.text_area("Document Description", "")
     ```
  2. Uncomment these lines and restart the application.

2. **Ask questions in the chat interface on the right side of the screen.**

   - Example of a question: **Highlight areas of energy waste in government facilities and suggest strategies to optimize usage. Quantify potential savings and environmental impacts.**





