from depedencies import *

# Load env & Settings
load_dotenv()

# Konfigurasi Settings
class Settings(BaseModel):
    # Azure OpenAI
    openai_key: str = os.getenv("azure-openai-api-key", "")
    openai_endpoint: str = os.getenv("azure-openai-endpoint", "")
    openai_api_version: str = os.getenv("azure-openai-api-version", "2024-05-01-preview")
    openai_deployment: str = os.getenv("azure-openai-deployment", "gpt-4o-mini")
    openai_embed_deployment: str = os.getenv("azure-openai-embed-deployment", "text-embedding-3-large")

    # Cognitive Search
    search_endpoint: str = os.getenv("azure-search-endpoint", "")
    search_key: str = os.getenv("azure-search-key", "")
    search_index: str = os.getenv("azure-search-index-name", "internal-docs-index")

    # Blob
    blob_conn: str = os.getenv("azure-blob-connection-string", "")
    blob_container: str = os.getenv("azure-blob-container", "internal-docs")

    # Document Intelligence
    docint_endpoint: str = os.getenv("azure-docint-endpoint", "")
    docint_key: str = os.getenv("azure-docint-key", "")

    # Azure Function (preprocess)
    func_preprocess_url: str = os.getenv("azure-function-preprocess-url", "")
    func_preprocess_key: str = os.getenv("azure-function-preprocess-key", "")

    # SQL
    sql_server: str = os.getenv("azure-sql-server", "")
    sql_db: str = os.getenv("azure-sql-database", "")
    sql_user: str = os.getenv("azure-sql-username", "")
    sql_password: str = os.getenv("azure-sql-password", "")

        # === Load dari .env ===
    MS_CLIENT_ID : str = os.getenv("ms-client-id","")
    MS_CLIENT_SECRET : str = os.getenv("ms-client-secret","")
    MS_TENANT_ID : str = os.getenv("ms-tenant-id","")
    MS_GRAPH_SCOPE : str = os.getenv("ms-graph-scope", "https://graph.microsoft.com/.default")
    MS_GROUP_ID : str = os.getenv("ms-group-id","")  # opsional, bisa kosong

    @property
    def ms_authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.MS_TENANT_ID}"
    

    # Notifications
    notify_webhook: str = os.getenv("notify-webhook-url", "")

    debug: bool = os.getenv("app-debug", "false").lower() == "true"

    #qdrant
    qdrant_url: str = os.getenv("qdrant-url","")
    qdrant_api_key: str = os.getenv("qdrant-api-key","")
    qdrant_collection: str = os.getenv("qdrant-collection","internal-docs-index")

    # Redis (Memory - Short Term)
    redis_host: str = os.getenv("redis-host", "")
    redis_port: int = int(os.getenv("redis-port", "6380"))
    redis_password: str = os.getenv("redis-password", "")
    redis_ssl: bool = os.getenv("redis-ssl", "true").lower() == "true"

    # Cosmos DB (Memory - Long Term)
    cosmos_endpoint: str = os.getenv("cosmos-endpoint", "")
    cosmos_key: str = os.getenv("cosmos-key", "")
    cosmos_database: str = os.getenv("cosmos-database", "internal_assistant")
    cosmos_container: str = os.getenv("cosmos-container", "conversation_history")

settings = Settings()


# =====================
# Core Clients
# =====================
llm = AzureChatOpenAI(
    azure_endpoint=settings.openai_endpoint,
    api_key=settings.openai_key,
    api_version=settings.openai_api_version,
    deployment_name=settings.openai_deployment,
    temperature=0.2,
)

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=settings.openai_endpoint,
    api_key=settings.openai_key,
    api_version=settings.openai_api_version,
    deployment=settings.openai_embed_deployment,
    chunk_size=32
)

# # VectorStore via azure ai search
# vectorstore = AzureSearch(
#     azure_search_endpoint=settings.search_endpoint,
#     azure_search_key=settings.search_key,
#     index_name=settings.search_index,
#     embedding_function=embeddings.embed_query,
# )

from qdrant_client import QdrantClient
import requests

print(f"🔗 Connecting to Qdrant at {settings.qdrant_url}")

try:
    import urllib3
    urllib3.disable_warnings()
    # Health check
    health = requests.get(f"{settings.qdrant_url}/healthz", timeout=5)
    print(f"Health check: {health.status_code} {health.text}")

    # Initialize client with longer timeout
    qdrant_client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
        timeout=60,
        prefer_grpc=False,
        https=True,
        verify=False,
        port=443
    )

    # Test connection by checking collections (lightweight operation)
    collections = qdrant_client.get_collections()
    print(f"✅ Connected to Qdrant. Collections: {len(collections.collections)}")

    # Initialize VectorStore with lazy loading
    vectorstoreQ = QdrantVectorStore(
        client=qdrant_client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )
    
    # Test if collection exists
    if qdrant_client.collection_exists(settings.qdrant_collection):
        retriever = vectorstoreQ.as_retriever(search_type="similarity", k=3)
        print("✅ Qdrant VectorStore initialized successfully")
    else:
        print(f"⚠️ Collection '{settings.qdrant_collection}' not found")
        retriever = None

except Exception as e:
    print(f"⚠️ Warning: Failed to initialize VectorStore: {e}")
    qdrant_client = None
    vectorstoreQ = None
    retriever = None




# vectorstoreQ = None
# retriever = None

# Blob
blob_service = BlobServiceClient.from_connection_string(settings.blob_conn)
blob_container = blob_service.get_container_client(settings.blob_container)

# Document Intelligence
doc_client = DocumentAnalysisClient(
    endpoint=settings.docint_endpoint,
    credential=AzureKeyCredential(settings.docint_key),
)

#for progressProject


# SQLAlchemy (optional, kept)
engine = None
# if settings.sql_server and settings.sql_db and settings.sql_user:
#     connection_string = URL.create(
#         "mssql+pyodbc",
#         username=settings.sql_user,
#         password=settings.sql_password,
#         host=settings.sql_server,
#         database=settings.sql_db,
#         query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
#     )
#     engine = sa.create_engine(connection_string, pool_pre_ping=True)

# =====================
# Import Tools dari modul lain
# =====================
from rag_modul import rag_tool
#from projectProgress_modul import project_tool, client_tool
from projectProgress_modul import (
    project_tool, project_detail_tool, project_list_tool, portfolio_analysis_tool,
)
from others import fetch_template_tool, notify_tool

# =====================
# Agent setup
# =====================
TOOLS = [
    rag_tool, project_tool, fetch_template_tool, notify_tool,
    project_detail_tool, project_list_tool, portfolio_analysis_tool,
    ]
#TOOLS = [rag_tool, project_tool, client_tool, fetch_template_tool, notify_tool]

SYSTEM_PROMPT = (
    "You are the company's Internal Assistant. You can: \n"
    "1) Jawab Q&A internal (qna_internal) – prefer when user asks policy/SOP.\n"
    "2) Cek status proyek (project_progress).\n"
    "3) Cek status client (client_status).\n"
    "4) Ambil template dokumen (fetch_template).\n"
    "5) Kirim notifikasi/pengingat (notify).\n\n"
    "Gunakan alat secara selektif. Jawaban harus ringkas dan berbasis sumber bila memungkinkan."
)

_agent_cache: Dict[str, AgentExecutor] = {}

def get_or_create_agent(user_id: str) -> AgentExecutor:
    if user_id in _agent_cache:
        return _agent_cache[user_id]
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = initialize_agent(
        tools=TOOLS,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=False,
        memory=memory,
        handle_parsing_errors=True,
    )
    # inject system prompt
    agent.agent.llm_chain.prompt.messages[0] = SystemMessage(content=SYSTEM_PROMPT)
    _agent_cache[user_id] = agent
    return agent

# =====================
# Memory Manager Initialization
# =====================
from memory_manager import initialize_memory_clients

redis_client, cosmos_container, memory_manager = initialize_memory_clients(settings)