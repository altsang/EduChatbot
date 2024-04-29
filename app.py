from flask import Flask, request, jsonify
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate

app = Flask(__name__)

folder_path = "db"

cached_llm = Ollama(model="mistral-7b")

embedding = FastEmbedEmbeddings()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
)

raw_prompt = PromptTemplate.from_template(
    """ 
    <s>[INST] You are a technical assistant good at searching documents. If you do not have an answer from the provided information say so. [/INST] </s>
    [INST] {input}
           Context: {context}
           Answer:
    [/INST]
"""
)

@app.route("/chatbot", methods=["POST"])
def chatbot():
    print("Post /chatbot called")
    json_content = request.json
    query = json_content.get("message", "")

    print(f"query: {query}")

    response = cached_llm.invoke(query)

    print(response)

    response_answer = {"answer": response}
    return jsonify(response_answer)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
