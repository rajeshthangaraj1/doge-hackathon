import os
import hashlib
import io
import json
from datetime import datetime
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from docx import Document
# from langchain.llms import OpenAI
from langchain_openai import ChatOpenAI



class FileHandler:
    def __init__(self, vector_db_path):
        self.vector_db_path = vector_db_path
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))



    def handle_file_upload(self, file, document_name, document_description):
        try:
            content = file.read()
            file_hash = hashlib.md5(content).hexdigest()
            file_key = f"{file.name}_{file_hash}"
            vector_store_dir = os.path.join(self.vector_db_path, file_key)
            os.makedirs(vector_store_dir, exist_ok=True)
            vector_store_path = os.path.join(vector_store_dir, "index.faiss")

            if os.path.exists(vector_store_path):
                return {"message": "File already processed."}

            # Process file based on type
            if file.name.endswith(".pdf"):
                texts = self.load_and_split_pdf(file)
            elif file.name.endswith(".docx"):
                texts = self.load_and_split_docx(file)
            elif file.name.endswith(".txt"):
                texts = self.load_and_split_txt(content)
            elif file.name.endswith(".xlsx"):
                texts = self.load_and_split_table(content)
            else:
                raise ValueError("Unsupported file format.")

            # Debugging: Verify the texts
            if not texts:
                return {"message": "No text extracted from the file. Check the file content."}

            # Create and save FAISS vector store
            vector_store = FAISS.from_texts(texts, self.embeddings)
            vector_store.save_local(vector_store_dir)

            metadata = {
                "filename": file.name,
                "document_name": document_name,
                "document_description": document_description,
                "file_size": len(content),
            }
            metadata_path = os.path.join(vector_store_dir, "metadata.json")
            with open(metadata_path, 'w') as md_file:
                json.dump(metadata, md_file)

            return {"message": "File processed successfully."}
        except Exception as e:
            return {"message": f"Error processing file: {str(e)}"}
    def load_and_split_pdf(self, file):
        reader = PdfReader(file)
        text = "".join([page.extract_text() for page in reader.pages])
        return self.split_text(text)

    def load_and_split_docx(self, file):
        doc = Document(file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return self.split_text(text)

    def load_and_split_txt(self, content):
        return self.split_text(content.decode("utf-8"))

    def load_and_split_table(self, content):
        excel_data = pd.read_excel(io.BytesIO(content), sheet_name=None)
        combined_text = ""
        for sheet_name, df in excel_data.items():
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)  # Drop empty rows/columns
            combined_text += f"\n\nSheet Name: {sheet_name}\n"
            combined_text += df.to_string(index=False)
        return self.split_text(combined_text)

    def split_text(self, text):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        return text_splitter.split_text(text)


class ChatHandler:
    def __init__(self, vector_db_path):
        self.vector_db_path = vector_db_path
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
        self.llm = ChatOpenAI(model="gpt-4", api_key=os.getenv('OPENAI_API_KEY'), max_tokens=150, temperature=0.2)

    def answer_question(self, question):
        responses = []
        for root, dirs, files in os.walk(self.vector_db_path):
            for dir in dirs:
                index_path = os.path.join(root, dir, "index.faiss")
                if os.path.exists(index_path):
                    vector_store = FAISS.load_local(
                        os.path.join(root, dir), self.embeddings, allow_dangerous_deserialization=True
                    )
                    # Use similarity_search_with_score instead of similarity_search
                    response_with_scores = vector_store.similarity_search_with_score(question, k=3)
                    print(response_with_scores)

                    # Filter responses based on score threshold
                    filtered_responses = [
                        doc.page_content for doc, score in response_with_scores if score > 0.3
                    ]
                    responses.extend(filtered_responses)

        if responses:
            prompt = self._generate_prompt(question, responses)
            print(prompt)
            return self.llm(prompt)
        return "No relevant documents found or context is insufficient to answer your question."

    def _generate_prompt(self, question, documents):
        """Generate a structured prompt with clear context and question focus."""
        context = "\n".join([f"Excerpt {i + 1}:\n{doc.strip()}" for i, doc in enumerate(documents[:3])])
        prompt = f"""
        You are an AI assistant that answers questions based on provided document excerpts.
        Your task is to analyze the context and provide a clear and accurate answer to the user's question.

        Context:
        {context}

        Question: {question}
        Answer concisely and clearly based on the context above. If additional calculations or interpretations are needed, provide them explicitly.
        """
        return prompt
