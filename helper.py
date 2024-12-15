import os
import hashlib
import io
import json
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from PyPDF2 import PdfReader
from docx import Document
import requests


class FileHandler:
    def __init__(self, vector_db_path,open_api_key,grok_api_key):
        self.vector_db_path = vector_db_path
        self.embeddings = OpenAIEmbeddings(api_key=open_api_key)
        self.grok_api_key = grok_api_key
        self.grok_base_url = "https://api.x.ai/v1"

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
            elif file.name.endswith(".csv"):
                texts, metadatas = self.load_and_split_csv(content)
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

    def load_and_split_csv(self, content):
        csv_data = pd.read_csv(io.StringIO(content.decode('utf-8')))
        texts = []
        metadatas = []
        csv_data = csv_data.dropna(how='all', axis=0).dropna(how='all', axis=1)
        csv_data = csv_data.fillna('N/A')
        for _, row in csv_data.iterrows():
            row_dict = row.to_dict()
            row_text = ', '.join([f"{key}: {value}" for key, value in row_dict.items()])
            texts.append(row_text)
            metadatas.append({"row_index": _})
        return texts, metadatas



class ChatHandler:
    def __init__(self, vector_db_path,open_api_key,grok_api_key):
        self.vector_db_path = vector_db_path
        self.embeddings = OpenAIEmbeddings(api_key=open_api_key)
        self.grok_base_url = "https://api.x.ai/v1"
        self.grok_api_key = grok_api_key

    def answer_question(self, question):
        responses = []
        for root, dirs, files in os.walk(self.vector_db_path):
            for dir in dirs:
                index_path = os.path.join(root, dir, "index.faiss")
                if os.path.exists(index_path):
                    vector_store = FAISS.load_local(
                        os.path.join(root, dir), self.embeddings, allow_dangerous_deserialization=True
                    )
                    response_with_scores = vector_store.similarity_search_with_relevance_scores(question, k=100)
                    filtered_responses = [doc.page_content for doc, score in response_with_scores]
                    responses.extend(filtered_responses)

        if responses:
            prompt = self._generate_prompt(question, responses)
            return self._ask_grok(prompt)

        return "No relevant documents found or context is insufficient to answer your question."

    def _ask_grok(self, prompt):
        # print('grok')
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
        Generate a structured prompt tailored to analyze government energy consumption data
        and answer questions effectively using the provided documents.
        """
        context = "\n".join(
            [f"Document {i + 1}:\n{doc.strip()}" for i, doc in enumerate(documents[:5])]
        )

        prompt = f"""
    You are an advanced AI assistant with expertise in energy data analysis, resource optimization, 
    and sustainability practices. Your role is to analyze government energy consumption data 
    to identify inefficiencies, propose actionable strategies, and quantify potential impacts.

    ### Data Provided:
    The following documents contain detailed information about energy productivity, consumption trends, 
    and inefficiencies in various sectors:
    {context}

    ### Question:
    {question}

    ### Instructions:
    1. **Highlight Areas of Energy Waste**:
       - Identify inefficiencies such as underutilized facilities, overconsumption in specific sectors, or
         energy system losses.
       - Use data points from the documents to back your observations.

    2. **Suggest Strategies for Optimization**:
       - Recommend actionable steps like upgrading equipment, adopting renewable energy sources,
         or optimizing resource allocation.
       - Ensure suggestions are feasible and tailored to the identified inefficiencies.

    3. **Demonstrate Cost-Saving and Environmental Benefits**:
       - Provide quantitative estimates of potential cost savings from the suggested strategies.
       - Highlight the environmental benefits, such as reductions in CO2 emissions or energy waste.

    4. **Present the Response Clearly**:
       - Organize your findings in a step-by-step format.
       - Use tables, bullet points, or concise paragraphs for clarity.

    ### Example Output Format:
    - **Energy Waste Identified**:
      1. ...
      2. ...

    - **Optimization Strategies**:
      1. ...
      2. ...

    - **Cost-Saving and Environmental Benefits**:
      - Savings: $...
      - Environmental Impact: ...

    Please ensure the response is data-driven, actionable, and easy to understand.
    """
        return prompt
