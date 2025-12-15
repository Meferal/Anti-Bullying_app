import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class RagExpert:
    def __init__(self, documents_dir: str = "./documents"):
        self.documents_dir = documents_dir
        self.vectorstores = {"parents": None, "teachers": None}
        self.chains = {"parents": None, "teachers": None}

        if os.environ.get("OPENAI_API_KEY"):
            self.refresh_knowledge_base()
        else:
            print("WARNING: RAG no inicializado. Falta OPENAI_API_KEY")

    def refresh_knowledge_base(self, force_rebuild: bool = False):
        """
        Carga documentos diferenciados por rol.
        Si existe un índice persistido y no se fuerza rebuild, lo carga.
        Si no, procesa docs y guarda el índice.
        """
        for role in ["parents", "teachers"]:
            try:
                role_dir = os.path.join(self.documents_dir, role)
                index_path = os.path.join(self.documents_dir, f"{role}_index")

                # 1. Intentar cargar desde disco
                is_outdated = self._is_index_outdated(role_dir, index_path)
                
                if not force_rebuild and not is_outdated and os.path.exists(index_path):
                    embeddings = OpenAIEmbeddings()
                    self.vectorstores[role] = FAISS.load_local(
                        index_path, 
                        embeddings, 
                        allow_dangerous_deserialization=True
                    )
                    self._build_chain(role)
                    print(f"Loaded existing RAG index for {role} from {index_path}")
                    continue
                
                if is_outdated:
                    print(f"Detected new changes in {role}. Rebuilding index...")

                # 2. Si no existe o forzamos o está desactualizado, construir de cero
                if not os.path.exists(role_dir):
                    os.makedirs(role_dir)
                    print(f"Created directory: {role_dir}")
                    continue

                docs = []
                for filename in os.listdir(role_dir):
                    filepath = os.path.join(role_dir, filename)
                    if filename.endswith(".txt"):
                        loader = TextLoader(filepath, encoding="utf-8")
                        docs.extend(loader.load())
                    elif filename.endswith(".pdf"):
                        loader = PyPDFLoader(filepath)
                        docs.extend(loader.load())
                    elif filename.endswith(".docx"):
                        from langchain_community.document_loaders import Docx2txtLoader
                        loader = Docx2txtLoader(filepath)
                        docs.extend(loader.load())
                
                if not docs:
                    print(f"No documents found for {role} in {role_dir}")
                    continue

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(docs)
                
                embeddings = OpenAIEmbeddings()
                self.vectorstores[role] = FAISS.from_documents(splits, embeddings)
                
                # 3. Guardar en disco para la próxima
                self.vectorstores[role].save_local(index_path)
                print(f"Saved RAG index for {role} to {index_path}")
                
                # Construir cadena específica para este rol
                self._build_chain(role)
                print(f"RAG Knowledge Base for {role} refreshed with {len(splits)} chunks.")
                
            except Exception as e:
                print(f"Error initializing RAG for {role}: {e}")

    def _is_index_outdated(self, role_dir: str, index_path: str) -> bool:
        """Compara la fecha de modificación del index con los archivos de documentos"""
        if not os.path.exists(index_path):
            return True # No existe, debe crearse
        
        if not os.path.exists(role_dir):
            return False # No hay docs, no hay nada que actualizar
            
        # Fecha de modificación del índice (asumimos la carpeta misma o index.faiss)
        index_mtime = os.path.getmtime(index_path)
        
        # Buscar archivo más reciente en documentos
        latest_doc_mtime = 0
        for root, dirs, files in os.walk(role_dir):
            for file in files:
                if file.endswith(('.txt', '.pdf', '.docx')):
                    file_path = os.path.join(root, file)
                    mtime = os.path.getmtime(file_path)
                    if mtime > latest_doc_mtime:
                        latest_doc_mtime = mtime
        
        # Si el doc más reciente es posterior al índice, está desactualizado
        return latest_doc_mtime > index_mtime

    def _build_chain(self, role):
        retriever = self.vectorstores[role].as_retriever(search_kwargs={"k": 2})
        
        # Prompts diferenciados
        if role == "parents":
            role_description = "un consejero empático para familias"
            context_instruction = "Usa lenguaje claro, tranquilizador y sin tecnicismos."
        else:
            role_description = "un experto técnico en protocolos escolares"
            context_instruction = "Usa terminología precisa, legal y enfócate en el procedimiento."

        template = f"""Eres {role_description}.
        Utiliza el siguiente contexto y el historial de conversación para responder.
        {context_instruction}
        Si la respuesta no está en el contexto, avisa y da una recomendación general.

        Contexto: {{context}}

        Historial Reciente:
        {{history}}

        Pregunta: {{question}}

        Respuesta:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        from operator import itemgetter

        self.chains[role] = (
            {
                "context": itemgetter("question") | retriever | format_docs, 
                "question": itemgetter("question"),
                "history": itemgetter("history")
            }
            | prompt
            | llm
            | StrOutputParser()
        )

    def get_advice(self, query: str, role: str = "parents", history: str = "") -> str:
        if role not in self.chains or not self.chains[role]:
            return f"El sistema RAG para '{role}' no está activo o no tiene documentos."
            
        # Invoke ahora espera un dict porque cambiamos el primer paso de la chain
        return self.chains[role].invoke({
            "question": query,
            "history": history
        })

rag_system = RagExpert()
