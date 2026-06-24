from flask import Flask, render_template, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import login
from dotenv import load_dotenv
import tempfile
import torch

load_dotenv()

app = Flask(__name__)

# Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
UPLOAD_FOLDER = 'documents'
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
EMBEDDINGS_MODEL = "paraphrase-multilingual-mpnet-base-v2"
CHROMA_DB_DIR = "chroma_db"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# GPU configuration
device = None
if torch.cuda.is_available():
    device = 'cuda'
    # Additional GPU optimization settings
    torch.backends.cudnn.benchmark = True
    torch.cuda.empty_cache()
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
else:
    device = 'cpu'
    print("Using CPU")

# Initialize embeddings with GPU support
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDINGS_MODEL,
    model_kwargs={'device': device},
    encode_kwargs={
        'normalize_embeddings': True,
        'batch_size': 32  # Increased batch size for GPU efficiency
    }
)
vector_store = None

headers = {
    'Authorization': f'Bearer {GROQ_API_KEY}',
    'Content-Type': 'application/json'
}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_documents():
    global vector_store
    documents = []

    # Load documents from UPLOAD_FOLDER
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if filename.endswith('.pdf'):
            try:
                loader = PyPDFLoader(filepath)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading PDF {filename}: {str(e)}")
        elif filename.endswith('.txt'):
            try:
                loader = TextLoader(filepath)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading text file {filename}: {str(e)}")

    if documents:
        # Split documents with improved configuration
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=128,
            length_function=len,
        )
        splits = text_splitter.split_documents(documents)

        # Create vector store with better error handling
        try:
            # Clear GPU cache before creating embeddings
            if device == 'cuda':
                torch.cuda.empty_cache()

            vector_store = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory=CHROMA_DB_DIR
            )
            vector_store.persist()
            return True
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            return False
    return False


# Try to load existing vector store
try:
    if os.path.exists(CHROMA_DB_DIR) and os.listdir(CHROMA_DB_DIR):
        # Clear GPU cache before loading
        if device == 'cuda':
            torch.cuda.empty_cache()

        vector_store = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings
        )
    else:
        vector_store = None
except Exception as e:
    print(f"Error loading existing vector store: {str(e)}")
    vector_store = None


@app.route('/')
def home():
    models = [
        {"id": "llama-3.3-70b-versatile","name":"Llama 3.3 70B"},
        {"id": "llama3-70b-8192", "name": "Llama 3 70B"},
        {"id":"deepseek-r1-distill-llama-70b","name":"DeepSeek R1 Distill Llama 70B"},
        #{"id":"mistral-saba-24b","name":"Mistral Saba 24B"},
        {"id":"gemma2-9b-it","name":"Gemma 2 Instruct"},
        {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "name": "Llama 4 Scout"},
        {"id": "llama3-8b-8192", "name": "Llama 3 8B"},
    ]
    return render_template('index.html', models=models)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process the document
            if process_documents():
                return jsonify({
                    "success": True,
                    "message": "File uploaded and processed successfully",
                    "filename": filename,
                    "device": device.upper()  # Show whether GPU was used
                })
            else:
                return jsonify({
                    "error": "File uploaded but processing failed",
                    "filename": filename
                }), 500
        except Exception as e:
            return jsonify({
                "error": f"Error processing file: {str(e)}",
                "filename": filename
            }), 500

    return jsonify({"error": "File type not allowed"}), 400


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    selected_model = request.json.get('model', 'mixtral-8x7b-32768')
    use_rag = request.json.get('use_rag', False)

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        if use_rag and vector_store:
            # Clear GPU cache before retrieval if using GPU
            if device == 'cuda':
                torch.cuda.empty_cache()

            # RAG-enhanced response
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )
            docs = retriever.get_relevant_documents(user_input)
            context = "\n\n".join([doc.page_content for doc in docs])

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Use the following context to answer the question. "
                               "If you don't know the answer, just say you don't know, don't try to make up an answer."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {user_input}\n\nAnswer:"
                }
            ]
        else:
            # Standard response
            messages = [
                {"role": "system", "content": "You are a helpful and smart assistant."},
                {"role": "user", "content": user_input}
            ]

        data = {
            "model": selected_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply, "device": device.upper()})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    except KeyError:
        return jsonify({"error": "Unexpected response format from API"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)