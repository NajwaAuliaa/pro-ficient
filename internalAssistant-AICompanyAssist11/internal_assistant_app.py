from depedencies import *
from azure.storage.blob import ContentSettings


from internal_assistant_core import (
    get_or_create_agent, settings,
    blob_container,
    qdrant_client,  
    memory_manager  
)

from rag_modul import (
    rag_answer, process_and_index_docs
)

# Project management imports dengan alias untuk menghindari konflik
from projectProgress_modul import (
    process_project_query, list_all_projects,
    analyze_project_data, generate_project_response,
    get_plans, get_plan_tasks, intelligent_project_query
)

# Todo management imports dengan alias untuk menghindari konflik
from to_do_modul_test import (
    # build_auth_url as todo_build_auth_url,
    # exchange_code_for_token as todo_exchange_code_for_token,
    # get_login_status as todo_get_login_status,
    process_todo_query_advanced,
    # is_user_logged_in as todo_is_user_logged_in,
)

from unified_auth import(
    build_unified_auth_url,
    exchange_unified_code_for_token,
    is_unified_authenticated,
    get_unified_login_status,
    get_authenticated_user_id,
    unified_token_manager as token_manager,
    clear_unified_token as clear_user_token
)

def set_user_token(token_data: dict, user_id: str = None):
    """Set user token using unified token manager with actual Microsoft user ID"""
    # Jika user_id tidak diberikan, coba ambil dari token_data
    if user_id is None:
        if "user_info" in token_data and "id" in token_data["user_info"]:
            user_id = token_data["user_info"]["id"]
        else:
            user_id = "current_user"  # fallback
    
    token_manager.set_token(user_id, token_data)
    print(f"Token set for user: {user_id}")

from documentManagement import (
    upload_file_to_blob,
    batch_upload_files,
    process_and_index_documents,
    upload_and_index_complete,
    list_documents_in_blob,
    delete_document_complete,     
    batch_delete_documents,       
    inspect_qdrant_collection_sample, 
    get_qdrant_collection_info,     
    rebuild_qdrant_index            
)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi import Request
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import os

app = FastAPI(title="Internal Assistant – LangChain + Azure + UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io",  # ✅ NEW FE URL
        "https://internal-assistant-backend.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io",
        "http://localhost:3000",  # Local development FE
        "http://localhost:8001",  # Local development BE
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    answer: str
    tool_calls: Optional[List[Dict[str, Any]]] = None

class IndexRequest(BaseModel):
    prefix: str = "sop/"

class DocumentDeleteRequest(BaseModel):
    blob_names: List[str]

# Enhanced System Prompt untuk lebih smart project handling
ENHANCED_SYSTEM_PROMPT = """
You are the company's Internal Assistant with advanced project management capabilities. You can:

1) **RAG Q&A Internal (qna_internal)** – Jawab pertanyaan policy/SOP, handbook dari dokumen internal, disini intinya adalah semua document yang hubungannya dengan internal company, dan anda harus menjawabnya sesuai dengan pertanyaan dari user. Jika konteks berasal dari beberapa potongan, gabungkan untuk menyusun jawaban lengkap”.
2) **Smart Project Progress (project_progress)** – Analisis mendalam project dari Microsoft Planner (REQUIRES LOGIN)
3) **Project List & Comparison** – List semua project atau bandingkan multiple projects  
4) **Client Status Check** – Cek status client
5) **Template Documents** – Ambil template dokumen
6) **Notifications** – Kirim notifikasi/pengingat
7) **Document Management** - Upload, list, delete, and manage documents in Azure Blob Storage

**ENHANCED PROJECT CAPABILITIES:**
- Deteksi otomatis project name dari natural language
- Analisis progress dengan insight dan recommendations
- Perbandingan multiple projects
- Identifikasi masalah (overdue tasks, bottlenecks)
- Smart suggestions untuk project management

**DOCUMENT MANAGEMENT CAPABILITIES:**
- Upload and automatically index documents
- List and manage existing documents
- Delete documents from both storage and search index
- Rebuild search indexes when needed

**AUTHENTICATION NOTE:**
- Project features require Microsoft login via delegated permissions with PKCE for SPA
- If user asks about projects but not authenticated, inform them to login first

**IMPORTANT DISTINCTION:**
- **PLANNER TASKS** = Project management tasks from Microsoft Planner (use project_progress tools)
- **TO-DO TASKS** = Personal tasks from Microsoft To-Do (use separate To-Do interface)

**USAGE GUIDELINES:**
- Untuk pertanyaan tentang PROJECT/PLANNER tasks, gunakan project_progress tool
- Untuk pertanyaan tentang personal TO-DO tasks, arahkan ke tab "Smart To-Do"
- Jika user tanya "list project" atau "semua project", gunakan project_list tool
- Untuk comparison, deteksi bila user menyebut 2+ project names
- Selalu berikan insight yang actionable dan highlight masalah penting
- Gunakan emoji untuk membuat response lebih engaging dan mudah dibaca

**KEYWORD DETECTION:**
- "project", "planner", "project management" → Use project tools
- "todo", "to-do", "personal task", "my tasks" → Direct to To-Do tab

**RESPONSE STYLE:**
- Professional namun friendly
- Gunakan format yang clear dengan bullet points atau sections
- Highlight urgent items dengan emoji peringatan  
- Berikan next steps recommendations
- Jawab dalam bahasa Indonesia kecuali diminta otherwise

Gunakan tools secara selektif dan berikan jawaban yang komprehensif namun tidak berlebihan.
"""

@app.get("/health")
def health():
    return {"ok": True, "service": "Internal Assistant – LangChain + Azure + UI (Fixed Version)"}

# ========== MEMORY MANAGEMENT ENDPOINTS ==========
@app.get("/memory/history/{user_id}")
def get_conversation_history(user_id: str, module: str = "rag", limit: int = 20):
    """Get conversation history for a user in specific module - user_id must be actual MS ID or guest_xxx

    OPTIMIZED: Reduced default limit from 100 to 20 for faster initial load
    """
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory system not available")

    # Validate user_id
    if not user_id or user_id in ["None", "null", "undefined"]:
        raise HTTPException(status_code=400, detail="Invalid user_id. User must be authenticated.")

    try:
        # Fast path: return minimal data structure for quick response
        history = memory_manager.get_recent_history(user_id, limit=limit, module=module)

        return {
            "user_id": user_id,
            "module": module,
            "message_count": len(history),
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@app.delete("/memory/session/{user_id}")
def clear_user_session(user_id: str, module: Optional[str] = None):
    """Clear Redis cache for user session (specific module or all) - user_id must be actual MS ID or guest_xxx"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory system not available")

    # Validate user_id
    if not user_id or user_id in ["None", "null", "undefined"]:
        raise HTTPException(status_code=400, detail="Invalid user_id. User must be authenticated.")

    try:
        memory_manager.clear_session(user_id, module=module)
        module_text = f"{module} module" if module else "all modules"
        return {
            "status": "success",
            "message": f"Session cleared for user: {user_id} ({module_text})"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@app.post("/clear-session")
def clear_session_endpoint(req: dict):
    """Clear chat history cache for current user"""
    try:
        user_id = req.get("user_id")
        module = req.get("module", "project")  # Default to project module
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
            
        if not memory_manager:
            raise HTTPException(status_code=503, detail="Memory system not available")
            
        memory_manager.clear_session(user_id, module=module)
        return {"status": "cleared", "user_id": user_id, "module": module}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/stats/{user_id}")
def get_user_memory_stats(user_id: str, module: Optional[str] = None):
    """Get conversation statistics for a user - user_id must be actual MS ID or guest_xxx"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory system not available")

    try:
        stats = memory_manager.get_user_statistics(user_id, module=module)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

# ========== UPLOAD & INDEX ENDPOINT ==========
def _detect_mime(path: str) -> str:
    ext = (os.path.splitext(path)[1] or "").lower()
    return {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".txt": "text/plain",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(ext, "application/octet-stream")
# ========== DOCUMENT MANAGEMENT ENDPOINTS ==========

@app.get("/documents")
def list_documents(prefix: str = "sop/"):
    """List all documents in blob storage with metadata"""
    try:
        documents = list_documents_in_blob(prefix, blob_container)
        return {
            "success": True,
            "prefix": prefix,
            "documents": documents,
            "total_documents": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...), prefix: str = Form("sop/")):
    """Upload multiple documents to blob storage and index them"""
    try:
        if not prefix.endswith("/"):
            prefix += "/"
        
        files_data = []
        for file in files:
            # Reset file pointer to beginning
            await file.seek(0)
            content = await file.read()
            
            print(f"DEBUG: File {file.filename} - Size: {len(content)} bytes, Content-Type: {file.content_type}")
            print(f"DEBUG: First 100 bytes: {content[:100]}")
            
            files_data.append({
                "filename": file.filename,
                "data": content,
                "content_type": file.content_type or _detect_mime(file.filename)
            })
        
        result = upload_and_index_complete(files_data, prefix, blob_container, settings)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading documents: {str(e)}")

@app.delete("/documents")
def delete_documents(request: DocumentDeleteRequest):
    """Delete multiple documents from both blob storage and search index"""
    try:
        result = batch_delete_documents(request.blob_names, blob_container, settings,qdrant_client)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting documents: {str(e)}")

@app.delete("/documents/{blob_name:path}")
def delete_single_document(blob_name: str):
    """Delete single document from both blob storage and search index"""
    try:
        result = delete_document_complete(blob_name, blob_container, settings,qdrant_client)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.get("/documents/inspect")
def inspect_documents(blob_name: Optional[str] = None, prefix: str = "sop/"):
    """Inspect search index structure and find documents (debugging tool)"""
    try:
        result = inspect_qdrant_collection_sample(settings, qdrant_client, blob_name) 
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inspecting index: {str(e)}")

@app.get("/documents/schema")
def get_index_schema():
    """Get search index schema information"""
    try:
        schema_info = get_qdrant_collection_info(settings,qdrant_client)
        return schema_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting schema: {str(e)}")

@app.post("/documents/reindex")
def reindex_documents(prefix: str = Query(default="sop/"), force: bool = Query(default=False)):
    try:
        print(f"[REINDEX] prefix={prefix}, force={force}")  # Debug log
        result = process_and_index_documents(prefix, blob_container, settings, force_reindex=force)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing documents: {str(e)}")

@app.post("/upload-and-index")
async def upload_and_index(
    files: List[UploadFile] = File(...),
    prefix: str = Form("sop/")
):
    uploaded = []
    errors = []
    if not prefix.endswith("/"):
        prefix += "/"
    for f in files:
        try:
            fname = f.filename
            blob_name = f"{prefix}{fname}"
            data = await f.read()
            content_type = _detect_mime(fname)
            blob_client = blob_container.get_blob_client(blob_name)
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )
            uploaded.append(blob_name)
        except Exception as e:
            errors.append(f"{fname}: {e}")
    index_report = process_and_index_docs(prefix=prefix)
    return {
        "uploaded": uploaded,
        "upload_errors": errors,
        "index_report": index_report
    }

# ========== RAG CHAT ENDPOINT ==========
@app.post("/rag-chat")
def rag_chat(req: dict):
    message = req.get("message", "")
    user_id = req.get("user_id", "guest_unknown")

    try:
        from internal_assistant_core import retriever
        docs = retriever.get_relevant_documents(message, k=10)
        
        answer = rag_answer(message, user_id=user_id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_name}")
def get_project_detail(project_name: str):
    """Enhanced API endpoint untuk detail project tertentu dengan SPA support"""
    try:
        if not is_unified_authenticated():
            return {
                "error": "Authentication required",
                "message": "Please login first via /project/login",
                "login_url": "/auth/microsoft",
                "authenticated": False,
                "client_type": "Single-Page Application (SPA)"
            }

        
         # Gunakan dynamic query
        result = intelligent_project_query(
            f"Give me detailed progress analysis of project {project_name} including tasks, completion rate, and any issues",
            "current_user"
        )
        return {
            "status": "success",
            "project_detail": result,
            "project_name": project_name,
            "authenticated": True,
            "client_type": "SPA",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Error fetching project detail: {str(e)}",
            "project_name": project_name,
            "authenticated": is_unified_authenticated(),
            "client_type": "SPA",
            "login_url": "/auth/microsoft" if not is_unified_authenticated() else None
        }


@app.get("/auth/microsoft")
def unified_microsoft_login():
    """Unified login endpoint untuk Todo dan Project Management"""
    try:
        auth_url = build_unified_auth_url()
        return RedirectResponse(auth_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Auth configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication service unavailable")

@app.get("/auth/callback")
def unified_callback(response: Response, code: str, state: str = None, error: str = None, error_description: str = None):
    """Unified callback untuk Todo dan Project Management - Returns simple HTML that triggers popup in opener"""
    import html

    print(f"DEBUG: Callback received - code: {code[:20] if code else 'None'}..., state: {state}")

    if error:
        print(f"DEBUG: OAuth error - {error}: {error_description}")
        safe_error = html.escape(error or "Unknown error")
        safe_description = html.escape(error_description or "Authentication was denied or cancelled")

        # User-friendly error message
        user_message = safe_description
        if "access_denied" in safe_error.lower() or "cancelled" in safe_description.lower():
            user_message = "Authentication was cancelled. Please try again if you want to access Microsoft features."
        elif "invalid" in safe_error.lower():
            user_message = "Invalid authentication request. Please contact your administrator."

        return HTMLResponse(f"""
            <html>
                <head><title>Authentication Failed</title></head>
                <body>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'auth_error',
                                title: 'Authentication Failed',
                                message: '{user_message}'
                            }}, 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io');
                            window.close();
                        }} else {{
                            window.location.href = 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io';
                        }}
                    </script>
                </body>
            </html>
        """)

    if not code:
        print("DEBUG: No code received")
        return HTMLResponse("""
            <html>
                <head><title>Authentication Error</title></head>
                <body>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({
                                type: 'auth_error',
                                title: 'Authentication Error',
                                message: 'Missing authorization code. Please try again.'
                            }, 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io');
                            window.close();
                        } else {
                            window.location.href = 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io';
                        }
                    </script>
                </body>
            </html>
        """)

    try:
        print("DEBUG: Attempting token exchange...")
        token = exchange_unified_code_for_token(code, state)
        print(f"DEBUG: Token exchange result: {token is not None}")

        if not token:
            raise ValueError("Token exchange failed")

        # Get user_id directly from token response
        user_id = None
        if token and "user_info" in token:
            user_id = token["user_info"].get('id')
            print(f"✅ DEBUG: Got user_id for session: {user_id}")
        else:
            print(f"⚠️ WARNING: No user_info in token response")

        print(f"DEBUG: Token stored successfully for user: {user_id}")

        # Create HTML response with postMessage to opener
        html_content = """
            <html>
                <head><title>Authentication Successful</title></head>
                <body>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({
                                type: 'auth_success',
                                title: 'Authentication Successful',
                            }, 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io');
                            window.close();
                        } else {
                            window.location.href = 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io?authenticated=true';
                        }
                    </script>
                </body>
            </html>
        """

        html_response = HTMLResponse(content=html_content)

        # Set session cookie if we have user_id
        if user_id:
            html_response.set_cookie(
                key="user_session",
                value=user_id,
                max_age=86400,  # 24 hours
                httponly=True,
                secure=True,  # REQUIRED for samesite=none
                samesite="none",  # Allow cross-subdomain cookie sharing
                domain=".whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io"  # Share across subdomains
            )
            print(f"✅ DEBUG: Session cookie set for user_id: {user_id}")

        return html_response
    except ValueError as e:
        print(f"DEBUG: ValueError in token exchange: {str(e)}")
        error_str = str(e)
        safe_error = html.escape(error_str)

        # User-friendly error message
        user_message = "Token exchange failed. Please try logging in again."
        if "expired" in error_str.lower():
            user_message = "Your authentication session has expired. Please login again."
        elif "invalid" in error_str.lower():
            user_message = "Invalid authentication token. Please try again."

        return HTMLResponse(f"""
            <html>
                <head><title>Authentication Failed</title></head>
                <body>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'auth_error',
                                title: 'Authentication Failed',
                                message: '{user_message}'
                            }}, 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io');
                            window.close();
                        }} else {{
                            window.location.href = 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io';
                        }}
                    </script>
                </body>
            </html>
        """)
    except Exception as e:
        print(f"DEBUG: Exception in token exchange: {str(e)}")
        error_str = str(e)
        safe_error = html.escape(error_str)

        # User-friendly error message
        user_message = "An unexpected error occurred during authentication. Please try again."
        if "network" in error_str.lower() or "connection" in error_str.lower():
            user_message = "Network error occurred. Please check your connection and try again."
        elif "timeout" in error_str.lower():
            user_message = "Authentication timed out. Please try again."

        return HTMLResponse(f"""
            <html>
                <head><title>Authentication Failed</title></head>
                <body>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'auth_error',
                                title: 'Authentication Failed',
                                message: '{user_message}'
                            }}, 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io');
                            window.close();
                        }} else {{
                            window.location.href = 'https://internalassistant-fe.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io';
                        }}
                    </script>
                </body>
            </html>
        """)

@app.get("/project/status")
def project_status():
    try:
        if is_unified_authenticated():
            return {
                "authenticated": True,
                "status": "✅ Sudah login Smart Project Management",
                "features_available": [
                    "Project Progress Analysis",
                    "Multi-Project Comparison",
                    "Portfolio Overview",
                    "Task Management Insights"
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "authenticated": False,
                "status": "❌ Belum login",
                "login_url": "/auth/microsoft"
            }
    except Exception as e:
        return {"authenticated": False, "status": f"Error: {str(e)}"}

@app.get("/todo/login-status")
def todo_login_status():
    try:
        if is_unified_authenticated():
            return {
                "authenticated": True,
                "status": "✅ Sudah login Microsoft To-Do"
            }
        else:
            return {
                "authenticated": False,
                "status": "❌ Belum login"
            }
    except Exception as e:
        return {
            "authenticated": False,
            "status": f"Error: {str(e)}"
        }

@app.post("/project-chat")
def project_chat(req: dict):
    message = req.get("message", "")
    user_id = req.get("user_id")
    
    if not user_id:
        return {"answer": "❌ User ID required"}

    try:
        if not is_unified_authenticated(user_id):
            return {"answer": "🔒 Authentication Required. Please login first"}

        result = intelligent_project_query(message, user_id)
        return {"answer": result}
    except Exception as e:
        return {"answer": f"❌ Error: {str(e)}"}

@app.post("/todo-chat")
def todo_chat(req: dict):
    message = req.get("message", "")
    user_id = req.get("user_id")
    
    if not user_id:
        return {"answer": "❌ User ID required"}
        
    try:
        if not is_unified_authenticated(user_id):
            return {"answer": "❌ Belum login. Silakan login terlebih dahulu."}

        answer = process_todo_query_advanced(message, user_id)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"❌ Error: {str(e)}"}
    
@app.get("/projects")
def get_all_projects():
    if not is_unified_authenticated():
        return {
            "error": "Authentication required",
            "message": "Please login first",
            "login_url": "/auth/microsoft",
            "authenticated": False
        }

    try:
        user_id = get_authenticated_user_id()
        result = list_all_projects(user_id)
        return {
            "status": "success",
            "projects": result,
            "authenticated": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "error": f"Error fetching projects: {str(e)}",
            "authenticated": True,
            "error_details": str(e)
        }

@app.get("/todo/examples")
def todo_examples():
    """Get contoh-contoh query todo"""
    examples = [
        "Tampilkan semua task saya",
        "Task apa saja yang deadline hari ini?",
        "Buatkan task baru: Review laporan keuangan deadline besok",
        "Tandai task 'Meeting pagi' sebagai selesai",
        "Task mana saja yang belum selesai?",
        "Berapa banyak task yang overdue?",
        "Buat reminder untuk call client deadline 5 September",
        "Ubah deadline task presentation jadi minggu depan",
        "Tunjukkan task yang sudah selesai bulan ini",
        "Ada task apa saja yang urgent?"
    ]
    return {"examples": examples}

@app.get("/todo/suggestions")
def todo_suggestions():
    """Get suggestions untuk todo management"""
    suggestions = """💡 Smart Suggestions:
- Analisis produktivitas saya minggu ini
- Task apa yang paling urgent?
- Buatkan planning task untuk project baru
- Reminder untuk follow up client besok

Tips:
- Gunakan bahasa natural, AI akan memahami maksud Anda
- Sebutkan deadline dengan jelas: "hari ini", "besok", "5 September"
- Deskripsi task bisa lebih detail untuk tracking yang better
- AI bisa membantu prioritisasi berdasarkan deadline dan urgency
"""
    return {"suggestions": suggestions}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Unified chat endpoint yang bisa handle semua jenis query
    """
    try:
        agent = get_or_create_agent(req.user_id)

        # Update system prompt with enhanced version
        from langchain.schema import SystemMessage
        agent.agent.llm_chain.prompt.messages[0] = SystemMessage(content=ENHANCED_SYSTEM_PROMPT)
        
        # Process query
        result = agent.invoke({"input": req.message})
        answer = result.get("output", "")
        steps = result.get("intermediate_steps", [])
        
        # Serialize tool calls for debugging
        serialized_steps = []
        for s in steps:
            try:
                action, observation = s
                serialized_steps.append({
                    "tool": getattr(action, "tool", None),
                    "tool_input": getattr(action, "tool_input", None),
                    "log": getattr(action, "log", None),
                    "observation": observation,
                })
            except Exception:
                pass
                
        return ChatResponse(answer=answer, tool_calls=serialized_steps)
        
    except Exception as e:
        if settings.debug:
            raise
        raise HTTPException(status_code=500, detail=str(e))

# Tambah endpoint debug
@app.get("/auth/debug")
def auth_debug():
    from unified_auth import unified_token_manager
    try:
        user_id = get_authenticated_user_id()
        token_data = unified_token_manager.get_token(user_id)
        return {
            "has_token": token_data is not None,
            "user_id": user_id,
            "token_keys": list(token_data.keys()) if token_data else None,
            "is_authenticated": is_unified_authenticated()
        }
    except:
        return {
            "has_token": False,
            "user_id": None,
            "token_keys": None,
            "is_authenticated": False
        }

@app.get("/auth/status")
def auth_status():
    return {
        "authenticated": is_unified_authenticated(),
        "status": get_unified_login_status() if is_unified_authenticated() else "Not logged in"
    }

@app.post("/auth/me")
def get_current_user(request: Request):
    """Get current authenticated user info - returns user_id for memory management

    Changed to POST to match frontend expectations (accepts empty body, reads from cookie)
    """
    try:
        from unified_auth import unified_token_manager

        # ONLY use cookie session - cross-subdomain cookie with domain=.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io
        user_id_from_cookie = request.cookies.get("user_session")
        print(f"[/auth/me] Checking cookie: {user_id_from_cookie}")

        if not user_id_from_cookie:
            print("[/auth/me] ❌ No session cookie found")
            raise Exception("No session cookie found")

        # Check if user_id from cookie has valid token
        if unified_token_manager.has_token(user_id_from_cookie):
            token_data = unified_token_manager.get_token(user_id_from_cookie)
            user_info = token_data.get("user_info")

            if user_info:
                print(f"[/auth/me] ✅ User authenticated: {user_info.get('displayName')}")
                return {
                    "authenticated": True,
                    "user_id": user_id_from_cookie,
                    "display_name": user_info.get('displayName'),
                    "email": user_info.get('mail') or user_info.get('userPrincipalName')
                }

        print(f"[/auth/me] ❌ No valid token for user_id: {user_id_from_cookie}")
        raise Exception("Invalid session")

    except Exception as e:
        print(f"[/auth/me] ❌ Error: {str(e)}")
        return {
            "authenticated": False,
            "user_id": None,
            "display_name": None,
            "email": None
        }

@app.post("/auth/logout")
def logout(response: Response, request: Request):
    """Logout endpoint that clears unified token and session cookie but preserves memory"""
    # Get user_id from cookie
    user_id = request.cookies.get("user_session")

    print(f"[DEBUG /auth/logout] Logging out user: {user_id}")

    try:
        from unified_auth import clear_unified_token
        # Only clear token, preserve memory for conversation history
        clear_unified_token()

        # Clear the session cookie with all necessary parameters
        # This ensures the cookie is deleted across all scenarios
        response.delete_cookie(
            key="user_session",
            path="/",
            samesite="none",
            httponly=True,
            secure=True  # Set to True if using HTTPS
        )
        print("[DEBUG /auth/logout] ✅ Session cookie cleared with all parameters")

        return {
            "status": "success",
            "message": "Successfully logged out",
            "authenticated": False
        }
    except Exception as e:
        print(f"[DEBUG /auth/logout] ⚠️ Logout error: {str(e)}")
        # Still clear cookie even if token clear fails
        response.delete_cookie(
            key="user_session",
            path="/",
            samesite="none",
            httponly=True,
            secure=True
        )
        return {
            "status": "error",
            "message": f"Logout error: {str(e)}",
            "authenticated": False
        }

@app.get("/debug/ideation")
def debug_ideation():
    """Debug endpoint khusus untuk project ideation"""
    from projectProgress_modul import analyze_project_data, get_plans, get_plan_tasks

    debug_result = {
        "timestamp": datetime.now().isoformat(),
        "authenticated": is_unified_authenticated(),
        "steps": []
    }

    try:
        # Step 1: Check authentication
        debug_result["steps"].append({
            "step": 1,
            "action": "Check authentication",
            "result": debug_result["authenticated"]
        })

        if not debug_result["authenticated"]:
            debug_result["error"] = "User not authenticated"
            return debug_result

        user_id = get_authenticated_user_id()

        # Step 2: Get all plans
        plans = get_plans(user_id=user_id)
        debug_result["steps"].append({
            "step": 2,
            "action": "Get all plans",
            "result": f"Found {len(plans)} plans",
            "plan_titles": [p.get('title', 'No title') for p in plans]
        })

        # Step 3: Find ideation project
        ideation_plan = None
        for p in plans:
            if "ideation" in p.get("title", "").lower():
                ideation_plan = p
                break

        debug_result["steps"].append({
            "step": 3,
            "action": "Find ideation project",
            "result": "Found" if ideation_plan else "Not found",
            "plan_info": ideation_plan if ideation_plan else None
        })

        if not ideation_plan:
            debug_result["error"] = "Ideation project not found"
            return debug_result

        # Step 4: Get tasks from ideation project
        plan_id = ideation_plan["id"]
        tasks = get_plan_tasks(plan_id, user_id)

        debug_result["steps"].append({
            "step": 4,
            "action": "Get tasks from ideation project",
            "result": f"Found {len(tasks)} tasks",
            "task_titles": [t.get('title', 'No title') for t in tasks[:5]]  # First 5 tasks
        })

        # Step 5: Full analysis
        analysis_result = analyze_project_data("ideation", user_id)

        debug_result["steps"].append({
            "step": 5,
            "action": "Full project analysis",
            "result": "Success" if "error" not in analysis_result else "Failed",
            "error": analysis_result.get("error") if "error" in analysis_result else None,
            "task_count": analysis_result.get("analysis", {}).get("total_tasks") if "error" not in analysis_result else None
        })

        debug_result["final_result"] = analysis_result

    except Exception as e:
        debug_result["exception"] = str(e)
        import traceback
        debug_result["traceback"] = traceback.format_exc()

    return debug_result

@app.get("/debug/analyze-project/{project_name}")
def debug_analyze_project(project_name: str):
    """Debug endpoint untuk analyze_project_data function"""
    from projectProgress_modul import analyze_project_data

    try:
        if not is_unified_authenticated():
            return {
                "error": "User not authenticated",
                "authenticated": False
            }

        user_id = get_authenticated_user_id()
        result = analyze_project_data(project_name, user_id)
        return {
            "project_name": project_name,
            "authenticated": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "project_name": project_name,
            "error": str(e),
            "authenticated": is_unified_authenticated(),
            "timestamp": datetime.now().isoformat()
        }

# Tambah endpoint untuk test Azure OpenAI langsung
@app.get("/debug/test-openai")
def test_openai_speed():
    import time
    
    start_time = time.time()
    
    try:
        from internal_assistant_core import llm
        
        # Test simple prompt
        response = llm.invoke("Hello, respond with just 'Hi'")
        
        end_time = time.time()
        
        return {
            "response": response.content,
            "time_taken": end_time - start_time,
            "model": "gpt-4.1",
            "status": "success"
        }
        
    except Exception as e:
        error_time = time.time() - start_time
        return {
            "error": str(e),
            "time_taken": error_time,
            "status": "failed"
        }

@app.get("/debug/test-qdrant")
def test_qdrant_speed():
    import time
    
    start_time = time.time()
    
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(url="http://localhost:6333", api_key=None)
        count = client.count("internal-docs-index").count
        
        end_time = time.time()
        
        return {
            "document_count": count,
            "time_taken": end_time - start_time,
            "status": "success"
        }
        
    except Exception as e:
        error_time = time.time() - start_time
        return {
            "error": str(e),
            "time_taken": error_time,
            "status": "failed"
        }

# ========== DEV RUN ==========
if __name__ == "__main__":
    import nest_asyncio
    import uvicorn
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)