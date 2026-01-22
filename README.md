# Pro-ficient: AI-Powered Internal Assistant

[![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=flat&logo=chainlink&logoColor=white)](https://www.langchain.com/)

**Pro-ficient** is an enterprise-grade AI-powered internal assistant designed to streamline document management, knowledge retrieval, and project collaboration within Microsoft 365 ecosystem. Built with cutting-edge AI technologies and seamlessly integrated with Azure services and Microsoft Graph API.

---

## 🌟 Key Features

### 1. **Intelligent Document Management & RAG (Retrieval-Augmented Generation)**
- **Smart Document Upload**: Support for multiple formats (PDF, DOCX, PPTX, XLSX, images)
- **AI-Powered Document Processing**: Automatic text extraction using Azure AI Document Intelligence
- **Advanced Vector Search**: Powered by Qdrant for semantic document retrieval
- **Conversational AI**: Chat with your documents using Azure OpenAI GPT-4
- **Context-Aware Responses**: Retrieves relevant information from your document repository
- **Multi-language Support**: Automatic language detection and processing

### 2. **Microsoft 365 Integration**
- **Microsoft Planner Integration**: 
  - View and manage project plans
  - Track tasks and buckets
  - Analyze project progress with AI insights
  - Natural language queries for project data
  
- **Microsoft To-Do Integration**:
  - Create, read, update, and delete tasks
  - Manage multiple task lists
  - Set due dates and priorities
  - AI-powered task management through conversational interface

- **Extensible Architecture**: Can integrate with any Microsoft Graph API service (Teams, Outlook, SharePoint, etc.)

### 3. **Conversational Memory & Context**
- **Short-term Memory**: Redis-based session management for real-time conversations
- **Long-term Memory**: Azure Cosmos DB for persistent conversation history
- **User-specific Context**: Personalized experience with user authentication
- **Multi-session Support**: Seamless conversation continuity across sessions

### 4. **Enterprise-Ready Security**
- **OAuth 2.0 Authentication**: Secure Microsoft account integration
- **Delegated Permissions**: User-specific access control
- **Token Management**: Automatic token refresh and secure storage
- **Azure-native Security**: Leverages Azure's enterprise security features

---

## 🏗️ Architecture

### Technology Stack

#### **Backend**
- **Framework**: FastAPI (Python)
- **AI/ML**: 
  - LangChain for orchestration
  - Azure OpenAI (GPT-4, Text Embedding 3 Large)
- **Vector Database**: Qdrant
- **Document Processing**: Azure AI Document Intelligence (Form Recognizer)
- **Storage**: Azure Blob Storage
- **Memory**:
  - Redis (short-term/session)
  - Azure Cosmos DB (long-term/persistent)
- **Authentication**: MSAL (Microsoft Authentication Library)

#### **Frontend**
- **Framework**: React.js
- **UI Components**: Custom components with Tailwind CSS
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Markdown Rendering**: Custom markdown renderer for AI responses

#### **Infrastructure**
- **Hosting**: Azure Container Apps
- **API Gateway**: Azure API Management (optional)
- **Monitoring**: Azure Application Insights (recommended)

---

## 📂 Project Structure

```
pro-ficient/
├── backend/
│   ├── internal_assistant_app.py       # FastAPI application & API endpoints
│   ├── internal_assistant_core.py      # Core setup (LangChain, Azure clients)
│   ├── rag_modul.py                    # RAG logic & document processing
│   ├── projectProgress_modul.py        # Microsoft Planner integration
│   ├── to_do_modul_test.py            # Microsoft To-Do integration
│   ├── documentManagement.py           # Document upload & indexing
│   ├── memory_manager.py               # Conversation memory management
│   ├── unified_auth.py                 # Unified authentication handler
│   ├── depedencies.py                  # Shared dependencies & utilities
│   ├── requirements.txt                # Python dependencies
│   ├── Dockerfile                      # Backend container configuration
│   ├── docker-compose.yml              # Local development setup
│   └── .env.example                    # Environment variables template
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RAGChatTab.js          # Document chat interface
│   │   │   ├── SmartProjectManagement.js  # Planner interface
│   │   │   ├── TodoTab.js             # To-Do interface
│   │   │   ├── UploadTab.js           # Document upload interface
│   │   │   ├── Sidebar.js             # Navigation sidebar
│   │   │   └── LandingPage.js         # Landing/login page
│   │   ├── contexts/
│   │   │   ├── chatcontext.js         # Chat state management
│   │   │   └── ThemeContext.js        # Theme management
│   │   ├── utils/
│   │   │   └── userIdManager.js       # User session management
│   │   ├── App.js                     # Main application component
│   │   └── index.js                   # Application entry point
│   ├── public/                         # Static assets
│   ├── package.json                    # Node.js dependencies
│   ├── Dockerfile                      # Frontend container configuration
│   ├── tailwind.config.js              # Tailwind CSS configuration
│   └── .env.production.example         # Frontend environment template
│
└── README.md                           # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Azure Subscription** with the following services:
  - Azure OpenAI Service
  - Azure Blob Storage
  - Azure AI Document Intelligence
  - Azure Cache for Redis
  - Azure Cosmos DB
  - Azure Container Apps (for deployment)

- **Microsoft 365 Account** with:
  - App registration in Azure AD
  - Microsoft Graph API permissions configured

- **Development Tools**:
  - Python 3.9+
  - Node.js 16+
  - Docker & Docker Compose (optional)
  - Git

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/pro-ficient.git
cd pro-ficient
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Azure credentials and API keys
```

**Required Environment Variables** (see `.env.example` for complete list):

```env
# Azure OpenAI
azure-openai-api-key=YOUR_KEY
azure-openai-endpoint=YOUR_ENDPOINT
azure-openai-deployment=gpt-4.1
azure-openai-embed-deployment=text-embedding-3-large

# Azure Blob Storage
azure-blob-connection-string=YOUR_CONNECTION_STRING
azure-blob-container=YOUR_CONTAINER_NAME

# Azure Document Intelligence
azure-docint-endpoint=YOUR_ENDPOINT
azure-docint-key=YOUR_KEY

# Microsoft Graph API
ms-client-id=YOUR_CLIENT_ID
ms-client-secret=YOUR_CLIENT_SECRET
ms-tenant-id=YOUR_TENANT_ID

# Qdrant Vector Database
qdrant-url=YOUR_QDRANT_URL
qdrant-collection=internal-docs-index

# Redis Cache
redis-host=YOUR_REDIS_HOST
redis-password=YOUR_REDIS_PASSWORD

# Cosmos DB
cosmos-endpoint=YOUR_COSMOS_ENDPOINT
cosmos-key=YOUR_COSMOS_KEY
```

#### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.production.example .env.production
# Edit .env.production with your backend URL
```

```env
REACT_APP_API_URL=http://localhost:8000  # For local development
```

#### 4. Run Locally

**Backend:**
```bash
cd backend
uvicorn internal_assistant_app:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm start
```

Access the application at `http://localhost:3000`

#### 5. Docker Deployment (Optional)

```bash
# Backend
cd backend
docker build -t pro-ficient-backend .
docker run -p 8000:8000 --env-file .env pro-ficient-backend

# Frontend
cd frontend
docker build -t pro-ficient-frontend .
docker run -p 3000:80 pro-ficient-frontend
```

---

## 🔧 Configuration

### Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Create new registration:
   - **Name**: Pro-ficient Internal Assistant
   - **Supported account types**: Single tenant
   - **Redirect URI**: `https://your-backend-url/auth/callback`

3. Configure API permissions:
   - Microsoft Graph:
     - `User.Read` (Delegated)
     - `Tasks.ReadWrite` (Delegated)
     - `Group.Read.All` (Delegated)
     - Add more as needed for additional Microsoft services

4. Generate client secret and note the values:
   - Application (client) ID
   - Directory (tenant) ID
   - Client secret value

### Qdrant Setup

**Option 1: Cloud (Recommended)**
- Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
- Create a cluster and collection
- Use the provided URL and API key

**Option 2: Self-hosted**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Create Collection:**
```python
# Run this once to initialize
python -c "from internal_assistant_core import qdrant_client; \
qdrant_client.create_collection(name='internal-docs-index', \
vectors_config={'size': 3072, 'distance': 'Cosine'})"
```

---

## 📖 Usage Guide

### 1. Document Management

**Upload Documents:**
1. Navigate to "Upload" tab
2. Select files (PDF, DOCX, PPTX, XLSX, images)
3. Click "Upload" - documents are automatically processed and indexed

**Chat with Documents:**
1. Go to "RAG Chat" tab
2. Ask questions about your documents
3. AI retrieves relevant context and provides accurate answers

**Example queries:**
- "What are the key points in the Q4 report?"
- "Summarize the project requirements document"
- "Find information about budget allocation"

### 2. Project Management (Microsoft Planner)

**View Projects:**
1. Navigate to "Project Management" tab
2. Authenticate with Microsoft account
3. View all plans and tasks

**AI-Powered Queries:**
- "Show me all overdue tasks"
- "What's the progress on Project X?"
- "List tasks assigned to John"
- "Analyze project completion rate"

### 3. Task Management (Microsoft To-Do)

**Manage Tasks:**
1. Go to "To-Do" tab
2. Authenticate with Microsoft account
3. Use natural language to manage tasks

**Example commands:**
- "Create a task: Review budget report, due tomorrow"
- "Show all my tasks for this week"
- "Mark task 'Send email' as complete"
- "What are my high-priority tasks?"

---

## 🔐 Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Rotate secrets regularly** - Update API keys and tokens periodically
3. **Use managed identities** - When deploying to Azure, use Managed Identity instead of connection strings
4. **Enable HTTPS** - Always use SSL/TLS in production
5. **Implement rate limiting** - Protect APIs from abuse
6. **Monitor access logs** - Use Azure Application Insights for security monitoring
7. **Principle of least privilege** - Grant minimum required permissions

---

## 🚢 Deployment to Azure

### Azure Container Apps (Recommended)

**Backend:**
```bash
# Build and push to Azure Container Registry
az acr build --registry yourregistry --image pro-ficient-backend:latest ./backend

# Deploy to Container Apps
az containerapp create \
  --name pro-ficient-backend \
  --resource-group your-rg \
  --image yourregistry.azurecr.io/pro-ficient-backend:latest \
  --environment your-env \
  --ingress external \
  --target-port 8000
```

**Frontend:**
```bash
# Build and push
az acr build --registry yourregistry --image pro-ficient-frontend:latest ./frontend

# Deploy
az containerapp create \
  --name pro-ficient-frontend \
  --resource-group your-rg \
  --image yourregistry.azurecr.io/pro-ficient-frontend:latest \
  --environment your-env \
  --ingress external \
  --target-port 80
```

### Environment Variables in Azure

Use Azure Container Apps environment variables or Azure Key Vault for secrets:

```bash
az containerapp update \
  --name pro-ficient-backend \
  --resource-group your-rg \
  --set-env-vars \
    azure-openai-api-key=secretref:openai-key \
    redis-password=secretref:redis-pwd
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

## 📊 Monitoring & Logging

- **Application Insights**: Monitor performance and errors
- **Log Analytics**: Query and analyze logs
- **Alerts**: Set up alerts for critical issues

```python
# Enable Application Insights in backend
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string='YOUR_CONNECTION_STRING'))
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Troubleshooting

### Common Issues

**1. Authentication Errors**
- Verify Azure AD app registration redirect URI
- Check client ID and tenant ID in `.env`
- Ensure required Graph API permissions are granted

**2. Document Processing Fails**
- Verify Azure Document Intelligence endpoint and key
- Check file format compatibility
- Ensure sufficient Azure quota

**3. Vector Search Not Working**
- Verify Qdrant connection
- Check if collection exists and is properly configured
- Ensure embeddings dimension matches (3072 for text-embedding-3-large)

**4. Redis Connection Issues**
- Verify Redis host and password
- Check if SSL is enabled (port 6380 for Azure Redis)
- Ensure firewall rules allow connection

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact: [your-email@example.com]
- Documentation: [Wiki](https://github.com/yourusername/pro-ficient/wiki)

---

## 🙏 Acknowledgments

- **Azure OpenAI** for powerful language models
- **LangChain** for AI orchestration framework
- **Qdrant** for vector search capabilities
- **Microsoft Graph API** for Microsoft 365 integration
- **FastAPI** for high-performance backend framework
- **React** for modern frontend development

---

## 🗺️ Roadmap

- [ ] Microsoft Teams integration
- [ ] SharePoint document sync
- [ ] Advanced analytics dashboard
- [ ] Multi-language UI support
- [ ] Mobile application
- [ ] Voice interface
- [ ] Custom workflow automation
- [ ] Integration with more Microsoft services (Outlook, OneNote, etc.)

---

**Built with ❤️ using Azure AI and Microsoft 365**
