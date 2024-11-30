import os
import hashlib
import io
import json
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import TextSplitter
from PyPDF2 import PdfReader
from docx import Document
from langchain_openai import ChatOpenAI
import requests


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
                texts, metadatas = self.load_and_split_pdf(file)
            elif file.name.endswith(".docx"):
                texts, metadatas = self.load_and_split_docx(file)
            elif file.name.endswith(".txt"):
                texts, metadatas = self.load_and_split_txt(content)
            elif file.name.endswith(".xlsx"):
                texts, metadatas = self.load_and_split_table(content)
            else:
                raise ValueError("Unsupported file format.")

            if not texts:
                return {"message": "No text extracted from the file. Check the file content."}

            vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
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
        texts = []
        metadatas = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                texts.append(text)
                metadatas.append({"page_number": page_num + 1})
        return texts, metadatas

    def load_and_split_docx(self, file):
        doc = Document(file)
        texts = []
        metadatas = []
        for para_num, paragraph in enumerate(doc.paragraphs):
            if paragraph.text:
                texts.append(paragraph.text)
                metadatas.append({"paragraph_number": para_num + 1})
        return texts, metadatas

    def load_and_split_txt(self, content):
        text = content.decode("utf-8")
        lines = text.split('\n')
        texts = [line for line in lines if line.strip()]
        metadatas = [{}] * len(texts)
        return texts, metadatas

    def load_and_split_table(self, content):
        excel_data = pd.read_excel(io.BytesIO(content), sheet_name=None)
        texts = []
        metadatas = []
        for sheet_name, df in excel_data.items():
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            df = df.fillna('N/A')
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                # Combine key-value pairs into a string
                row_text = ', '.join([f"{key}: {value}" for key, value in row_dict.items()])
                texts.append(row_text)
                metadatas.append({"sheet_name": sheet_name})
        return texts, metadatas



class ChatHandler:
    def __init__(self, vector_db_path):
        self.vector_db_path = vector_db_path
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
        self.llm_openai = ChatOpenAI(
            model_name="gpt-4",
            api_key=os.getenv('OPENAI_API_KEY'),
            max_tokens=500,
            temperature=0.2,
        )
        self.grok_base_url = "https://api.x.ai/v1"
        self.grok_api_key = os.getenv('GROK_API_KEY')

    def answer_question(self, question, model_choice):
        responses = []
        for root, dirs, files in os.walk(self.vector_db_path):
            for dir in dirs:
                index_path = os.path.join(root, dir, "index.faiss")
                if os.path.exists(index_path):
                    vector_store = FAISS.load_local(
                        os.path.join(root, dir), self.embeddings, allow_dangerous_deserialization=True
                    )
                    response_with_scores = vector_store.similarity_search_with_relevance_scores(question, k=5)
                    filtered_responses = [doc.page_content for doc, score in response_with_scores]
                    responses.extend(filtered_responses)

        if responses:
            prompt = self._generate_prompt(question, responses)
            if model_choice == "OpenAI":
                return self._ask_openai(prompt)
            elif model_choice == "Grok":
                return self._ask_grok(prompt)

        return "No relevant documents found or context is insufficient to answer your question."

    def _ask_openai(self, prompt):
        print('openai')
        llm_response = self.llm_openai.generate([prompt])
        if llm_response and llm_response.generations and llm_response.generations[0]:
            return llm_response.generations[0][0].text.strip()
        else:
            return "Could not extract an answer."

    def _ask_grok(self, prompt):
        print('grok')
        endpoint = f"{self.grok_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "grok-beta",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.2,
        }
        response = requests.post(endpoint, headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            # print("Grok API Response:", response_json)  # For debugging purposes
            # Extract the content from the 'choices' array
            choices = response_json.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"]["content"].strip()
            else:
                return "Response format unexpected: Could not extract the answer."
        else:
            return f"Error: {response.status_code}, {response.text}"

    def _generate_prompt(self, question, documents):

        """
        Generate a structured and detailed prompt for the RAG model to answer questions based on provided documents.
        The response should be step-by-step, accurate, and optimized for analytical queries.
        """
        context = "\n".join([f"Document {i + 1}:\n{doc.strip()}" for i, doc in enumerate(documents[:5])])
        prompt = f"""
            You are an advanced AI assistant specializing in analyzing complex queries and providing precise, actionable insights.
            You have access to the following data:
            
            {context}
            
            Based on this data, please answer the following question:
            
            Question: {question}
            
            Instructions:
            - Analyze the provided data carefully.
            - Provide a detailed, step-by-step response addressing the question.
            - Support your answer with specific data points from the context.
            - If data is missing, state that additional information is required.
            - Present your answer in a clear and concise manner.
            """
        return prompt