import os
import requests
import json
import re
from urllib.parse import urlencode
from internal_assistant_core import settings, llm, memory_manager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
# Use unified auth functions directly
# ====================
# Modul Microsoft To Do (Authorization Code Flow – Delegated)
# ====================

# Ambil config dari settings/env
CLIENT_ID = settings.MS_CLIENT_ID
TENANT_ID = settings.MS_TENANT_ID
REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI", "https://internal-assistant-backend.whitecliff-cbbdbf53.southeastasia.azurecontainerapps.io/auth/callback")

_token_cache = {}

# ====================
# Authentication Functions
# ====================


def get_current_token(user_id: str):
    """Ambil access_token dari unified token manager - REQUIRED user_id"""
    from unified_auth import get_unified_token
    return get_unified_token(user_id)


# ====================
# Microsoft Graph API Functions
# ====================

def get_todo_lists(user_id: str, token: dict = None):
    """Ambil semua To Do lists user - REQUIRED user_id"""
    try:
        access_token = token["access_token"] if token else get_current_token(user_id)
        url = "https://graph.microsoft.com/v1.0/me/todo/lists"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Token expired. Silakan login ulang.")
        raise Exception(f"Error API: {e.response.status_code} - {e.response.text}")

def get_todo_tasks(user_id: str, list_id: str, token: dict = None):
    """Ambil semua task dari sebuah list - REQUIRED user_id"""
    try:
        access_token = token["access_token"] if token else get_current_token(user_id)
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Token expired. Silakan login ulang.")
        elif e.response.status_code == 404:
            raise Exception(f"List dengan ID '{list_id}' tidak ditemukan.")
        raise Exception(f"Error API: {e.response.status_code} - {e.response.text}")

def get_all_tasks(user_id: str):
    """Ambil semua tasks dari semua lists - REQUIRED user_id"""
    try:
        access_token = get_current_token(user_id)

        # Dapetin semua lists dulu
        lists_data = get_todo_lists(user_id)
        all_tasks = []

        for todo_list in lists_data.get("value", []):
            list_id = todo_list["id"]
            list_name = todo_list["displayName"]

            # Ambil tasks untuk setiap list
            tasks_data = get_todo_tasks(user_id, list_id)
            for task in tasks_data.get("value", []):
                task["list_name"] = list_name
                task["list_id"] = list_id
                all_tasks.append(task)

        return all_tasks
    except Exception as e:
        raise Exception(f"Error getting all tasks: {str(e)}")

def create_todo_task(user_id: str, list_id: str, title: str, body: str = "", due_date: str = None):
    """Buat task baru dalam list tertentu - REQUIRED user_id"""
    try:
        access_token = get_current_token(user_id)
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        task_data = {
            "title": title,
            "body": {
                "content": body,
                "contentType": "text"
            }
        }

        # Tambahkan due date jika ada
        if due_date:
            task_data["dueDateTime"] = {
                "dateTime": due_date,
                "timeZone": "UTC"
            }

        resp = requests.post(url, headers=headers, json=task_data)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Token expired. Silakan login ulang.")
        raise Exception(f"Error membuat task: {e.response.status_code} - {e.response.text}")

def complete_todo_task(user_id: str, list_id: str, task_id: str):
    """Mark task sebagai completed - REQUIRED user_id"""
    try:
        access_token = get_current_token(user_id)
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        task_data = {
            "status": "completed"
        }

        resp = requests.patch(url, headers=headers, json=task_data)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Token expired. Silakan login ulang.")
        raise Exception(f"Error completing task: {e.response.status_code} - {e.response.text}")

def update_todo_task(user_id: str, list_id: str, task_id: str, title: str = None, body: str = None, due_date: str = None):
    """Update task yang sudah ada - REQUIRED user_id"""
    try:
        access_token = get_current_token(user_id)
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        task_data = {}
        if title:
            task_data["title"] = title
        if body:
            task_data["body"] = {"content": body, "contentType": "text"}
        if due_date:
            task_data["dueDateTime"] = {"dateTime": due_date, "timeZone": "UTC"}
        
        resp = requests.patch(url, headers=headers, json=task_data)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Token expired. Silakan login ulang.")
        raise Exception(f"Error updating task: {e.response.status_code} - {e.response.text}")

def find_default_list_id(user_id: str) -> str:
    """Cari default list (biasanya 'Tasks' atau list pertama) - REQUIRED user_id"""
    try:
        lists_data = get_todo_lists(user_id)
        lists = lists_data.get("value", [])

        # Cari list dengan nama 'Tasks' atau 'My Tasks'
        for todo_list in lists:
            name = todo_list.get('displayName', '').lower()
            if name in ['tasks', 'my tasks', 'task']:
                return todo_list['id']

        # Jika tidak ada, ambil list pertama
        if lists:
            return lists[0]['id']

        raise Exception("Tidak ada To-Do list ditemukan.")
    except Exception as e:
        raise Exception(f"Error finding default list: {str(e)}")

# ====================
# GRAPH API REQUEST HANDLER
# ====================

def graph_api_request(endpoint: str, method: str = "GET", data: dict = None, user_id: str = "current_user") -> dict:
    """Generic Graph API request handler"""
    try:
        access_token = get_current_token(user_id)
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        if method == "GET":
            resp = requests.get(url, headers=headers)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            resp = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        resp.raise_for_status()

        # Return empty dict for DELETE or if no content
        if method == "DELETE" or resp.status_code == 204:
            return {"success": True}

        return resp.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Token expired. Please login again.")
        raise Exception(f"API Error: {e.response.status_code} - {e.response.text}")

# ====================
# LANGCHAIN TOOL FUNCTIONS (Dynamic API Access)
# ====================

def tool_get_all_lists(user_id: str) -> str:
    """Get all To-Do lists for the user. Use this to see available lists."""
    try:
        result = graph_api_request("/me/todo/lists", user_id=user_id)
        lists = result.get("value", [])

        if not lists:
            return "No To-Do lists found."

        output = ["Available To-Do Lists:"]
        for lst in lists:
            list_id = lst.get("id", "")
            display_name = lst.get("displayName", "Unnamed")
            is_default = lst.get("isOwner", False)
            output.append(f"- {display_name} (ID: {list_id}) {'[DEFAULT]' if is_default else ''}")

        return "\n".join(output)
    except Exception as e:
        return f"Error getting lists: {str(e)}"

def tool_get_tasks_from_list(list_id: str, user_id: str) -> str:
    """Get all tasks from a specific list. Provide the list_id."""
    try:
        if not list_id or not list_id.strip():
            return "Error: list_id is required"

        result = graph_api_request(f"/me/todo/lists/{list_id}/tasks", user_id=user_id)
        tasks = result.get("value", [])

        if not tasks:
            return f"No tasks found in list {list_id}"

        output = [f"Tasks in list {list_id}:"]
        for task in tasks:
            title = task.get("title", "Untitled")
            task_id = task.get("id", "")
            status = task.get("status", "notStarted")
            due_date = task.get("dueDateTime", {}).get("dateTime", "No deadline")
            importance = task.get("importance", "normal")

            status_icon = "✅" if status == "completed" else "⏳"
            priority_icon = "🔴" if importance == "high" else ""

            output.append(f"- {status_icon} {priority_icon} {title} (ID: {task_id}, Status: {status}, Due: {due_date})")

        return "\n".join(output)
    except Exception as e:
        return f"Error getting tasks: {str(e)}"

def tool_get_all_tasks(user_id: str) -> str:
    """Get ALL tasks from ALL lists. Use this for comprehensive task overview."""
    try:
        # First get all lists
        lists_result = graph_api_request("/me/todo/lists", user_id=user_id)
        lists = lists_result.get("value", [])

        if not lists:
            return "No To-Do lists found."

        all_tasks_info = []
        current_date = datetime.now().date()

        for lst in lists:
            list_id = lst.get("id")
            list_name = lst.get("displayName", "Unnamed")

            # Get tasks for this list
            tasks_result = graph_api_request(f"/me/todo/lists/{list_id}/tasks", user_id=user_id)
            tasks = tasks_result.get("value", [])

            for task in tasks:
                task_info = {
                    "list_name": list_name,
                    "list_id": list_id,
                    "task_id": task.get("id"),
                    "title": task.get("title", "Untitled"),
                    "status": task.get("status", "notStarted"),
                    "importance": task.get("importance", "normal"),
                    "body": task.get("body", {}).get("content", ""),
                    "created": task.get("createdDateTime", ""),
                    "last_modified": task.get("lastModifiedDateTime", "")
                }

                # Parse due date
                due_info = task.get("dueDateTime")
                if due_info:
                    due_date_str = due_info.get("dateTime", "")
                    try:
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
                        days_diff = (due_date - current_date).days

                        task_info["due_date"] = due_date.isoformat()
                        task_info["days_until_due"] = days_diff

                        if days_diff < 0:
                            task_info["due_status"] = f"OVERDUE ({abs(days_diff)} days)"
                        elif days_diff == 0:
                            task_info["due_status"] = "DUE TODAY"
                        elif days_diff == 1:
                            task_info["due_status"] = "DUE TOMORROW"
                        else:
                            task_info["due_status"] = f"Due in {days_diff} days"
                    except Exception:
                        task_info["due_date"] = due_date_str
                        task_info["due_status"] = "Unknown"
                else:
                    task_info["due_date"] = None
                    task_info["due_status"] = "No deadline"

                all_tasks_info.append(task_info)

        if not all_tasks_info:
            return "No tasks found across all lists."

        # Format output
        output = [f"Total tasks found: {len(all_tasks_info)}\n"]

        # Group by list
        from itertools import groupby
        all_tasks_info.sort(key=lambda x: x["list_name"])

        for list_name, tasks_group in groupby(all_tasks_info, key=lambda x: x["list_name"]):
            tasks_list = list(tasks_group)
            output.append(f"\n📋 {list_name} ({len(tasks_list)} tasks):")

            for task in tasks_list:
                status_icon = "✅" if task["status"] == "completed" else "⏳"
                priority_icon = "🔴" if task["importance"] == "high" else ""

                task_line = f"  {status_icon} {priority_icon} {task['title']}"

                if task["due_status"] != "No deadline":
                    task_line += f" | {task['due_status']}"

                output.append(task_line)

        return "\n".join(output)
    except Exception as e:
        return f"Error getting all tasks: {str(e)}"

def tool_get_task_details(list_id: str, task_id: str, user_id: str) -> str:
    """Get detailed information about a specific task. Provide list_id and task_id."""
    try:
        if not list_id or not task_id:
            return "Error: Both list_id and task_id are required"

        result = graph_api_request(f"/me/todo/lists/{list_id}/tasks/{task_id}", user_id=user_id)

        output = ["Task Details:"]
        output.append(f"Title: {result.get('title', 'Untitled')}")
        output.append(f"Status: {result.get('status', 'notStarted')}")
        output.append(f"Importance: {result.get('importance', 'normal')}")

        body = result.get("body", {}).get("content", "")
        if body:
            output.append(f"Description: {body}")

        due_date = result.get("dueDateTime", {}).get("dateTime", "")
        if due_date:
            output.append(f"Due Date: {due_date}")

        output.append(f"Created: {result.get('createdDateTime', 'Unknown')}")
        output.append(f"Last Modified: {result.get('lastModifiedDateTime', 'Unknown')}")

        # Check for linked resources
        if result.get("hasAttachments"):
            output.append("Has attachments: Yes")

        return "\n".join(output)
    except Exception as e:
        return f"Error getting task details: {str(e)}"

def tool_create_task(list_id: str, title: str, user_id: str, body: str = "", due_date: str = "", importance: str = "normal") -> str:
    """
    Create a new task in a specific list.
    Args:
        list_id: ID of the list to add task to
        title: Task title (required)
        user_id: User ID (required)
        body: Task description (optional)
        due_date: Due date in ISO format YYYY-MM-DD (optional)
        importance: Task importance - 'low', 'normal', or 'high' (optional, default: normal)
    """
    try:
        if not list_id or not title:
            return "Error: list_id and title are required"

        task_data = {
            "title": title.strip(),
            "importance": importance if importance in ["low", "normal", "high"] else "normal"
        }

        if body and body.strip():
            task_data["body"] = {
                "content": body.strip(),
                "contentType": "text"
            }

        if due_date and due_date.strip():
            # Try to parse and validate date
            try:
                parsed_date = datetime.fromisoformat(due_date.strip())
                task_data["dueDateTime"] = {
                    "dateTime": parsed_date.isoformat(),
                    "timeZone": "UTC"
                }
            except ValueError:
                return f"Error: Invalid due_date format. Use YYYY-MM-DD or ISO format. Got: {due_date}"

        result = graph_api_request(f"/me/todo/lists/{list_id}/tasks", method="POST", data=task_data, user_id=user_id)

        return f"✅ Task created successfully!\nTask ID: {result.get('id')}\nTitle: {result.get('title')}"
    except Exception as e:
        return f"Error creating task: {str(e)}"

def tool_update_task(list_id: str, task_id: str, user_id: str, title: str = "", body: str = "", due_date: str = "", importance: str = "", status: str = "") -> str:
    """
    Update an existing task.
    Args:
        list_id: List ID
        task_id: Task ID
        user_id: User ID (required)
        title: New title (optional)
        body: New description (optional)
        due_date: New due date in ISO format (optional)
        importance: New importance level (optional)
        status: New status - 'notStarted', 'inProgress', 'completed' (optional)
    """
    try:
        if not list_id or not task_id:
            return "Error: list_id and task_id are required"

        task_data = {}

        if title and title.strip():
            task_data["title"] = title.strip()

        if body and body.strip():
            task_data["body"] = {
                "content": body.strip(),
                "contentType": "text"
            }

        if due_date and due_date.strip():
            try:
                parsed_date = datetime.fromisoformat(due_date.strip())
                task_data["dueDateTime"] = {
                    "dateTime": parsed_date.isoformat(),
                    "timeZone": "UTC"
                }
            except ValueError:
                return f"Error: Invalid due_date format: {due_date}"

        if importance and importance in ["low", "normal", "high"]:
            task_data["importance"] = importance

        if status and status in ["notStarted", "inProgress", "completed"]:
            task_data["status"] = status

        if not task_data:
            return "Error: No update fields provided"

        result = graph_api_request(f"/me/todo/lists/{list_id}/tasks/{task_id}", method="PATCH", data=task_data, user_id=user_id)

        return f"✅ Task updated successfully!\nTask: {result.get('title')}"
    except Exception as e:
        return f"Error updating task: {str(e)}"

def tool_complete_task(list_id: str, task_id: str, user_id: str) -> str:
    """Mark a task as completed. Provide list_id and task_id."""
    try:
        if not list_id or not task_id:
            return "Error: list_id and task_id are required"

        task_data = {"status": "completed"}
        result = graph_api_request(f"/me/todo/lists/{list_id}/tasks/{task_id}", method="PATCH", data=task_data, user_id=user_id)

        return f"✅ Task completed!\nTask: {result.get('title')}"
    except Exception as e:
        return f"Error completing task: {str(e)}"

def tool_delete_task(list_id: str, task_id: str, user_id: str) -> str:
    """Delete a task permanently. Provide list_id and task_id."""
    try:
        if not list_id or not task_id:
            return "Error: list_id and task_id are required"

        graph_api_request(f"/me/todo/lists/{list_id}/tasks/{task_id}", method="DELETE", user_id=user_id)

        return f"✅ Task deleted successfully (List: {list_id}, Task: {task_id})"
    except Exception as e:
        return f"Error deleting task: {str(e)}"

def tool_search_tasks(query: str, user_id: str) -> str:
    """
    Search for tasks by title across all lists. Provide search query.
    Returns matching tasks with their IDs and list information.
    """
    try:
        if not query or not query.strip():
            return "Error: Search query is required"

        # Get all tasks first
        lists_result = graph_api_request("/me/todo/lists", user_id=user_id)
        lists = lists_result.get("value", [])

        if not lists:
            return "No lists found."

        query_lower = query.lower().strip()
        matches = []

        for lst in lists:
            list_id = lst.get("id")
            list_name = lst.get("displayName", "Unnamed")

            tasks_result = graph_api_request(f"/me/todo/lists/{list_id}/tasks", user_id=user_id)
            tasks = tasks_result.get("value", [])

            for task in tasks:
                title = task.get("title", "")
                if query_lower in title.lower():
                    matches.append({
                        "list_name": list_name,
                        "list_id": list_id,
                        "task_id": task.get("id"),
                        "title": title,
                        "status": task.get("status", "notStarted")
                    })

        if not matches:
            return f"No tasks found matching '{query}'"

        output = [f"Found {len(matches)} task(s) matching '{query}':\n"]
        for match in matches:
            status_icon = "✅" if match["status"] == "completed" else "⏳"
            output.append(f"{status_icon} {match['title']}")
            output.append(f"   List: {match['list_name']}")
            output.append(f"   IDs: list_id={match['list_id']}, task_id={match['task_id']}\n")

        return "\n".join(output)
    except Exception as e:
        return f"Error searching tasks: {str(e)}"

# ====================
# RAW TASK DATA RETRIEVAL (for LLM analysis with deadline info)
# ====================

def tool_get_all_tasks_json(user_id: str) -> str:
    """Get ALL tasks as structured JSON with deadline details for LLM analysis.

    Returns raw task data so LLM can answer deadline questions accurately.
    Unlike tool_get_all_tasks which returns formatted text,
    this returns JSON that LLM can parse and analyze deadline information.
    """
    try:
        # First get all lists
        lists_result = graph_api_request("/me/todo/lists", user_id=user_id)
        lists = lists_result.get("value", [])

        if not lists:
            return json.dumps({"success": False, "message": "No To-Do lists found"})

        all_tasks = []

        for lst in lists:
            list_id = lst.get("id")
            list_name = lst.get("displayName", "Unnamed")

            # Get tasks for this list
            tasks_result = graph_api_request(f"/me/todo/lists/{list_id}/tasks", user_id=user_id)
            tasks = tasks_result.get("value", [])

            for task in tasks:
                # Extract and structure deadline info
                due_date = None
                due_status = None

                if task.get("dueDateTime"):
                    try:
                        due_date_str = task["dueDateTime"].get("dateTime", "")
                        if due_date_str:
                            due_date_obj = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
                            due_date = due_date_obj.isoformat()

                            days_diff = (due_date_obj - datetime.now().date()).days
                            if days_diff < 0:
                                due_status = f"OVERDUE ({abs(days_diff)} days ago)"
                            elif days_diff == 0:
                                due_status = "DUE TODAY"
                            elif days_diff == 1:
                                due_status = "DUE TOMORROW"
                            else:
                                due_status = f"Due in {days_diff} days"
                    except Exception as e:
                        pass

                task_obj = {
                    "list_id": list_id,
                    "list_name": list_name,
                    "task_id": task.get("id"),
                    "title": task.get("title", "Untitled"),
                    "status": task.get("status", "notStarted"),
                    "importance": task.get("importance", "normal"),
                    "due_date": due_date,
                    "due_status": due_status,
                    "completed": task.get("status") == "completed"
                }

                all_tasks.append(task_obj)

        result = {
            "success": True,
            "total_tasks": len(all_tasks),
            "tasks": all_tasks
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

# ====================
# LANGCHAIN TOOLS SETUP
# ====================

def create_todo_tools(user_id: str):
    """Create LangChain tools for To-Do operations with user context"""
    tools = [
        Tool(
            name="get_all_lists",
            func=lambda query="": tool_get_all_lists(user_id),
            description="Get all To-Do lists. Use this first to see available lists and their IDs."
        ),
        Tool(
            name="get_tasks_from_list",
            func=lambda list_id: tool_get_tasks_from_list(list_id, user_id),
            description="Get all tasks from a specific list. Input: list_id (string)"
        ),
        Tool(
            name="get_all_tasks",
            func=lambda query="": tool_get_all_tasks(user_id),
            description="Get ALL tasks from ALL lists with comprehensive details including due dates, status, priority. Best for overview and analysis."
        ),
        Tool(
            name="get_task_details",
            func=lambda input_str: tool_get_task_details(*input_str.split(","), user_id),
            description="Get detailed info about a specific task. Input: 'list_id,task_id'"
        ),
        Tool(
            name="create_task",
            func=lambda input_str: tool_create_task(*input_str.split("|"), user_id) if len(input_str.split("|")) >= 2 else tool_create_task(input_str.split("|")[0] if "|" in input_str else "", input_str, user_id),
            description="Create new task. Input: 'list_id|title|body|due_date|importance' (body, due_date, importance are optional, separate with |)"
        ),
        Tool(
            name="update_task",
            func=lambda input_str: tool_update_task(*input_str.split("|")[:2], user_id, *input_str.split("|")[2:]),
            description="Update task. Input: 'list_id|task_id|title|body|due_date|importance|status' (all except IDs optional, separate with |)"
        ),
        Tool(
            name="complete_task",
            func=lambda input_str: tool_complete_task(*input_str.split(","), user_id),
            description="Mark task as completed. Input: 'list_id,task_id'"
        ),
        Tool(
            name="delete_task",
            func=lambda input_str: tool_delete_task(*input_str.split(","), user_id),
            description="Delete task permanently. Input: 'list_id,task_id'"
        ),
        Tool(
            name="search_tasks",
            func=lambda query: tool_search_tasks(query, user_id),
            description="Search tasks by title across all lists. Input: search query (string)"
        )
    ]
    return tools

# ====================
# AGENT CREATION WITH MEMORY
# ====================

def create_todo_agent(user_id: str):
    """Create a ReAct agent for To-Do management with user context"""
    tools = create_todo_tools(user_id)

    # Enhanced prompt template for To-Do assistant
    template = """You are a Smart Microsoft To-Do Assistant with direct access to Microsoft Graph API.

Current Date: {current_date}
User Timezone: Asia/Jakarta

You have access to these tools to interact with Microsoft To-Do:
{tools}

Tool Names: {tool_names}

IMPORTANT INSTRUCTIONS:
1. When user asks about tasks, use get_all_tasks for comprehensive overview
2. Always get list IDs first using get_all_lists before creating/updating tasks
3. For searches, use search_tasks to find tasks by title
4. Be proactive - if user wants to complete a task but didn't provide IDs, search for it first
5. Format dates as YYYY-MM-DD when creating/updating tasks
6. Provide helpful, actionable responses in Indonesian
7. Use emojis to make responses engaging

Use this format:

Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer in Indonesian with helpful formatting

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    prompt = PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tools", "tool_names", "current_date"],
        template=template
    )

    # Create agent
    agent = create_react_agent(llm, tools, prompt)

    # Create executor with verbose output
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        max_execution_time=60,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    return agent_executor

# ====================
# Utility Functions for Task Management
# ====================

def format_task_display(tasks: List[Dict], show_list_name: bool = True) -> str:
    """Format tasks untuk display yang rapi"""
    if not tasks:
        return "📝 Tidak ada task ditemukan."
    
    result = []
    current_date = datetime.now().date()
    
    # Group tasks by status
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    pending_tasks = [t for t in tasks if t.get("status") != "completed"]
    
    # Show pending tasks first
    if pending_tasks:
        result.append("## ⏳ *Task yang Belum Selesai:*\n")
        for i, task in enumerate(pending_tasks, 1):
            task_line = format_single_task(task, i, show_list_name, current_date)
            result.append(task_line)
        result.append("")
    
    # Show completed tasks
    if completed_tasks:
        result.append("## ✅ *Task yang Sudah Selesai:*\n")
        for i, task in enumerate(completed_tasks, 1):
            task_line = format_single_task(task, i, show_list_name, current_date)
            result.append(task_line)
    
    return "\n".join(result)

def format_single_task(task: Dict, index: int, show_list_name: bool, current_date) -> str:
    """Format single task untuk display"""
    title = task.get('title', 'Untitled Task')
    status = task.get('status', 'notStarted')
    
    # Status icon
    status_icon = "✅" if status == "completed" else "⏳"
    
    # Build task line
    task_parts = [f"{index}. {status_icon} *{title}*"]
    
    # Add list name if requested
    if show_list_name and 'list_name' in task:
        task_parts.append(f"(dalam {task['list_name']})")
    
    # Add due date if exists
    if task.get('dueDateTime'):
        try:
            due_date_str = task['dueDateTime']['dateTime']
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
            
            # Calculate days difference
            days_diff = (due_date - current_date).days
            
            if days_diff < 0:
                date_info = f"🔴 *OVERDUE* ({abs(days_diff)} hari)"
            elif days_diff == 0:
                date_info = "🟡 *HARI INI*"
            elif days_diff == 1:
                date_info = "🟠 *BESOK*"
            else:
                date_info = f"📅 {due_date.strftime('%d/%m/%Y')}"
            
            task_parts.append(f"- {date_info}")
        except Exception:
            pass
    
    # Add body/description if exists
    if task.get('body', {}).get('content'):
        content = task['body']['content'].strip()
        if content and len(content) > 0:
            # Truncate long content
            if len(content) > 100:
                content = content[:100] + "..."
            task_parts.append(f"\n   📝 {content}")
    
    return " ".join(task_parts)

def find_task_by_title(tasks: List[Dict], title: str) -> Optional[Dict]:
    """Cari task berdasarkan title (fuzzy matching)"""
    title_lower = title.lower().strip()
    
    # Exact match first
    for task in tasks:
        if task.get('title', '').lower() == title_lower:
            return task
    
    # Partial match
    for task in tasks:
        task_title = task.get('title', '').lower()
        if title_lower in task_title or task_title in title_lower:
            return task
    
    return None

# ====================
# LLM-Based Query Processing
# ====================

def process_todo_query(query: str, token: dict) -> str:
    """Main function untuk process query user menggunakan LLM"""
    try:
        if not query.strip():
            return "📝 Silakan masukkan pertanyaan atau perintah terkait To-Do Anda."
        
        # Get current tasks data
        all_tasks = get_all_tasks()
        
        # Prepare context for LLM
        tasks_context = prepare_tasks_context(all_tasks)
        
        # Create system prompt untuk Todo Assistant
        system_prompt = """You are a Smart Microsoft To-Do Assistant. You help users manage their tasks using natural language.

Available Actions:
1. VIEW/LIST tasks - Show tasks with various filters
2. CREATE new tasks 
3. COMPLETE existing tasks
4. UPDATE existing tasks

Current Date: {current_date}

Context about user's tasks:
{tasks_context}

Guidelines:
- Analyze user intent from their natural language query
- For CREATE: Extract task title, description, and due date if mentioned
- For COMPLETE: Find the task by title (use fuzzy matching)
- For VIEW: Apply appropriate filters (today, completed, pending, etc.)
- Always respond in Indonesian with helpful formatting
- Use emojis to make responses engaging
- Provide specific actionable information

Respond with a JSON object containing:
{{
    "intent": "view|create|complete|update",
    "action": {{
        "type": "detected_action_type",
        "parameters": {{"relevant_parameters"}}
    }},
    "response": "formatted_response_for_user"
}}""".format(
            current_date=datetime.now().strftime('%Y-%m-%d'),
            tasks_context=tasks_context
        )
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User query: {query}")
        ]
        
        llm_response = llm.invoke(messages)
        
        # Parse LLM response
        try:
            response_data = json.loads(llm_response.content)
        except json.JSONDecodeError:
            # Fallback jika LLM tidak return valid JSON
            return fallback_process_query(query, all_tasks)
        
        # Execute action based on LLM decision
        return execute_llm_action(response_data, all_tasks, token)
        
    except Exception as e:
        return f"❌ *Error:* {str(e)}\n\n💡 *Tip:* Pastikan Anda sudah login dan coba gunakan perintah yang lebih spesifik."

def prepare_tasks_context(tasks: List[Dict]) -> str:
    """Prepare context string untuk LLM tentang current tasks"""
    if not tasks:
        return "User belum memiliki task apapun."
    
    context_parts = []
    current_date = datetime.now().date()
    
    # Summary statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
    pending_tasks = total_tasks - completed_tasks
    
    context_parts.append(f"Total tasks: {total_tasks} (Completed: {completed_tasks}, Pending: {pending_tasks})")
    
    # Recent tasks
    recent_tasks = sorted(tasks, key=lambda x: x.get('createdDateTime', ''), reverse=True)[:10]
    
    context_parts.append("\nRecent Tasks:")
    for task in recent_tasks:
        title = task.get('title', 'Untitled')
        status = task.get('status', 'notStarted')
        list_name = task.get('list_name', 'Unknown List')
        
        status_emoji = "✅" if status == "completed" else "⏳"
        
        # Check due date
        due_info = ""
        if task.get('dueDateTime'):
            try:
                due_date_str = task['dueDateTime']['dateTime']
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
                days_diff = (due_date - current_date).days
                
                if days_diff < 0:
                    due_info = f" (OVERDUE {abs(days_diff)} days)"
                elif days_diff == 0:
                    due_info = " (DUE TODAY)"
                elif days_diff == 1:
                    due_info = " (DUE TOMORROW)"
                elif days_diff <= 7:
                    due_info = f" (due in {days_diff} days)"
            except Exception:
                pass
        
        context_parts.append(f"- {status_emoji} {title} (List: {list_name}){due_info}")
    
    return "\n".join(context_parts)

def execute_llm_action(response_data: Dict, all_tasks: List[Dict], token: dict) -> str:
    """Execute action yang sudah dianalisis oleh LLM"""
    try:
        intent = response_data.get("intent", "view")
        action = response_data.get("action", {})
        llm_response = response_data.get("response", "")
        
        if intent == "create":
            return handle_create_task_llm(action, token, llm_response)
        elif intent == "complete":
            return handle_complete_task_llm(action, all_tasks, token, llm_response)
        elif intent == "update":
            return handle_update_task_llm(action, all_tasks, token, llm_response)
        else:
            # View tasks
            return handle_view_tasks_llm(action, all_tasks, llm_response)
            
    except Exception as e:
        # Return LLM response if action execution fails
        return response_data.get("response", f"❌ Error executing action: {str(e)}")

def handle_create_task_llm(action: Dict, token: dict, llm_response: str) -> str:
    """Handle create task berdasarkan LLM analysis"""
    try:
        params = action.get("parameters", {})
        title = params.get("title", "").strip()
        
        if not title:
            return "❌ Judul task tidak boleh kosong. Coba lagi dengan format yang lebih jelas."
        
        # Find default list
        default_list_id = find_default_list_id()
        
        # Extract optional parameters
        body = params.get("description", "")
        due_date = params.get("due_date")
        
        # Parse due date if it's in text format
        if due_date and isinstance(due_date, str):
            due_date = parse_due_date(due_date)
        
        # Create task
        created_task = create_todo_task(default_list_id, title, body, due_date)
        
        # Generate success response
        response_parts = [
            "✅ *Task berhasil dibuat!*",
            "",
            f"📝 *Judul:* {created_task.get('title')}",
            f"📋 *List:* Tasks (Default)"
        ]
        
        if due_date:
            due_date_formatted = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
            response_parts.append(f"📅 *Deadline:* {due_date_formatted}")
        
        if body:
            response_parts.append(f"📝 *Deskripsi:* {body}")
        
        response_parts.extend([
            "",
            "💡 *Tips:* Anda bisa mengatakan 'Tandai task [nama] sebagai selesai' untuk menyelesaikan task ini nanti."
        ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error membuat task: {str(e)}"

def handle_complete_task_llm(action: Dict, all_tasks: List[Dict], token: dict, llm_response: str) -> str:
    """Handle complete task berdasarkan LLM analysis"""
    try:
        params = action.get("parameters", {})
        task_title = params.get("task_title", "").strip()
        
        if not task_title:
            return "❌ Nama task tidak ditemukan. Coba format: 'Tandai task [nama task] sebagai selesai'"
        
        # Find task
        target_task = find_task_by_title(all_tasks, task_title)
        
        if not target_task:
            # Use LLM to suggest similar tasks
            return suggest_similar_tasks(task_title, all_tasks)
        
        # Check if already completed
        if target_task.get("status") == "completed":
            return f"ℹ Task *'{target_task.get('title')}'* sudah ditandai sebagai selesai sebelumnya."
        
        # Complete the task
        completed_task = complete_todo_task(target_task['list_id'], target_task['id'])
        
        response_parts = [
            "🎉 *Task berhasil diselesaikan!*",
            "",
            f"✅ *Task:* {completed_task.get('title')}",
            f"📋 *List:* {target_task.get('list_name', 'Unknown')}",
            f"⏰ *Diselesaikan pada:* {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "",
            "🎯 *Great job!* Satu task lagi selesai!"
        ]
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error menyelesaikan task: {str(e)}"

def handle_view_tasks_llm(action: Dict, all_tasks: List[Dict], llm_response: str) -> str:
    """Handle view tasks berdasarkan LLM analysis"""
    try:
        # Use LLM response if it's well formatted
        if llm_response and "❌" not in llm_response and len(llm_response) > 50:
            return llm_response
        
        # Fallback to formatted task display
        if not all_tasks:
            return "📝 Anda belum memiliki task apapun. Coba buat task baru dengan mengatakan: 'Buatkan task baru: [nama task]'"
        
        # Apply filters from action parameters
        filtered_tasks = apply_llm_filters(all_tasks, action.get("parameters", {}))
        
        # Generate summary
        total_tasks = len(all_tasks)
        filtered_count = len(filtered_tasks)
        completed_count = len([t for t in all_tasks if t.get("status") == "completed"])
        pending_count = total_tasks - completed_count
        
        response_parts = [
            "📋 *Daftar Task Anda:*",
            "",
            format_task_display(filtered_tasks),
            "",
            "---",
            f"📊 *Summary:* {filtered_count} task ditampilkan dari total {total_tasks} task",
            f"✅ Selesai: {completed_count} | ⏳ Belum selesai: {pending_count}"
        ]
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error mengambil tasks: {str(e)}"

def handle_update_task_llm(action: Dict, all_tasks: List[Dict], token: dict, llm_response: str) -> str:
    """Handle update task berdasarkan LLM analysis"""
    try:
        params = action.get("parameters", {})
        task_title = params.get("task_title", "").strip()
        
        if not task_title:
            return "❌ Nama task untuk update tidak ditemukan."
        
        # Find task
        target_task = find_task_by_title(all_tasks, task_title)
        
        if not target_task:
            return suggest_similar_tasks(task_title, all_tasks)
        
        # Extract update parameters
        new_title = params.get("new_title")
        new_description = params.get("new_description") 
        new_due_date = params.get("new_due_date")
        
        if new_due_date and isinstance(new_due_date, str):
            new_due_date = parse_due_date(new_due_date)
        
        # Update task
        updated_task = update_todo_task(
            target_task['list_id'], 
            target_task['id'], 
            new_title, 
            new_description, 
            new_due_date
        )
        
        response_parts = [
            "✅ *Task berhasil diupdate!*",
            "",
            f"📝 *Task:* {updated_task.get('title')}",
            f"📋 *List:* {target_task.get('list_name', 'Unknown')}"
        ]
        
        if new_due_date:
            due_date_formatted = datetime.fromisoformat(new_due_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
            response_parts.append(f"📅 *Deadline Baru:* {due_date_formatted}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error mengupdate task: {str(e)}"

def suggest_similar_tasks(search_title: str, all_tasks: List[Dict]) -> str:
    """Gunakan LLM untuk suggest similar tasks"""
    try:
        # Prepare task titles for LLM
        task_titles = [task.get('title', '') for task in all_tasks if task.get("status") != "completed"]
        
        if not task_titles:
            return f"❌ Task dengan nama '{search_title}' tidak ditemukan dan tidak ada task lain yang tersedia."
        
        system_prompt = f"""You are helping find similar task names. User searched for: '{search_title}'

Available task titles:
{chr(10).join([f"- {title}" for title in task_titles])}

Find the 3 most similar task titles to '{search_title}' and return them as a JSON array.
Example: ["Task 1", "Task 2", "Task 3"]

Return only the JSON array, nothing else."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Find similar tasks to: {search_title}")
        ]
        
        llm_response = llm.invoke(messages)
        
        try:
            similar_titles = json.loads(llm_response.content)
            if isinstance(similar_titles, list) and similar_titles:
                response_parts = [
                    f"❌ Task dengan nama '{search_title}' tidak ditemukan.",
                    "",
                    "🔍 *Apakah maksud Anda salah satu dari ini?*",
                    ""
                ]
                for title in similar_titles[:5]:
                    response_parts.append(f"• {title}")
                
                return "\n".join(response_parts)
        except:
            pass
        
        # Fallback to basic similarity
        return f"❌ Task dengan nama '{search_title}' tidak ditemukan. Gunakan 'Tampilkan semua task' untuk melihat daftar task Anda."
        
    except Exception:
        return f"❌ Task dengan nama '{search_title}' tidak ditemukan."

def apply_llm_filters(tasks: List[Dict], filter_params: Dict) -> List[Dict]:
    """Apply filters berdasarkan LLM analysis"""
    filtered_tasks = tasks.copy()
    current_date = datetime.now().date()
    
    # Date filters
    date_filter = filter_params.get("date_filter")
    if date_filter == "today":
        filtered_tasks = [t for t in filtered_tasks if is_task_due_today(t, current_date)]
    elif date_filter == "tomorrow":
        tomorrow = current_date + timedelta(days=1)
        filtered_tasks = [t for t in filtered_tasks if is_task_due_on_date(t, tomorrow)]
    elif date_filter == "week":
        week_end = current_date + timedelta(days=7)
        filtered_tasks = [t for t in filtered_tasks if is_task_due_in_range(t, current_date, week_end)]
    elif date_filter == "overdue":
        filtered_tasks = [t for t in filtered_tasks if is_task_overdue(t, current_date)]
    
    # Status filters
    status_filter = filter_params.get("status_filter")
    if status_filter:
        filtered_tasks = [t for t in filtered_tasks if t.get("status") == status_filter]
    
    # Show only tasks with deadlines
    if filter_params.get("show_deadlines", False):
        filtered_tasks = [t for t in filtered_tasks if t.get('dueDateTime')]
    
    return filtered_tasks

def is_task_due_today(task: Dict, current_date) -> bool:
    """Check apakah task due hari ini"""
    try:
        if not task.get('dueDateTime'):
            return False
        due_date_str = task['dueDateTime']['dateTime']
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        return due_date == current_date
    except Exception:
        return False

def is_task_due_on_date(task: Dict, target_date) -> bool:
    """Check apakah task due pada tanggal tertentu"""
    try:
        if not task.get('dueDateTime'):
            return False
        due_date_str = task['dueDateTime']['dateTime']
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        return due_date == target_date
    except Exception:
        return False

def is_task_due_in_range(task: Dict, start_date, end_date) -> bool:
    """Check apakah task due dalam range tanggal"""
    try:
        if not task.get('dueDateTime'):
            return False
        due_date_str = task['dueDateTime']['dateTime']
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        return start_date <= due_date <= end_date
    except Exception:
        return False

def is_task_overdue(task: Dict, current_date) -> bool:
    """Check apakah task sudah overdue"""
    try:
        if not task.get('dueDateTime') or task.get("status") == "completed":
            return False
        due_date_str = task['dueDateTime']['dateTime']
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        return due_date < current_date
    except Exception:
        return False

def parse_due_date(date_text: str) -> Optional[str]:
    """Parse text due date ke ISO format"""
    try:
        date_text_lower = date_text.lower().strip()
        
        if "hari ini" in date_text_lower or "today" in date_text_lower:
            return datetime.now().isoformat()
        elif "besok" in date_text_lower or "tomorrow" in date_text_lower:
            return (datetime.now() + timedelta(days=1)).isoformat()
        elif "minggu depan" in date_text_lower or "next week" in date_text_lower:
            return (datetime.now() + timedelta(days=7)).isoformat()
        
        # Try parsing common date formats
        date_patterns = [
            r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})",  # DD/MM/YYYY or DD-MM-YYYY
            r"(\d{2,4})[\/\-](\d{1,2})[\/\-](\d{1,2})",  # YYYY/MM/DD or YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    # Assume DD/MM/YYYY format for first pattern
                    if pattern == date_patterns[0]:
                        day, month, year = match.groups()
                        if len(year) == 2:
                            year = "20" + year
                        target_date = datetime(int(year), int(month), int(day))
                    else:
                        # YYYY/MM/DD format
                        year, month, day = match.groups()
                        target_date = datetime(int(year), int(month), int(day))
                    
                    return target_date.isoformat()
                except ValueError:
                    continue
        
        return None
    except Exception:
        return None

def fallback_process_query(query: str, all_tasks: List[Dict], user_id: str) -> str:
    """Fallback processing jika LLM response tidak valid - user_id untuk future use"""
    query_lower = query.lower()

    # Simple pattern matching as fallback
    if any(word in query_lower for word in ["buat", "tambah", "create", "add"]):
        return "📝 Untuk membuat task baru, gunakan format: 'Buatkan task baru: [nama task]'"

    elif any(word in query_lower for word in ["selesai", "complete", "done", "tandai"]):
        return "✅ Untuk menyelesaikan task, gunakan format: 'Tandai task [nama task] sebagai selesai'"

    else:
        # Default to showing all tasks
        if not all_tasks:
            return "📝 Anda belum memiliki task apapun. Coba buat task baru dengan mengatakan: 'Buatkan task baru: [nama task]'"

        return format_task_display(all_tasks)

# ====================
# MAIN QUERY PROCESSING WITH AGENT & MEMORY
# ====================

def process_todo_query_advanced(query: str, user_id: str) -> str:
    """
    Process To-Do query using dynamic agent with conversation memory.
    Module: "todo" (separated from rag and project)
    """
    if not query.strip():
        return """📝 **Selamat datang di Smart To-Do Assistant!**

Saya adalah asisten AI dengan akses langsung ke Microsoft To-Do Anda. Saya bisa:

**📋 Melihat & Menganalisis:**
• "Tampilkan semua task saya"
• "Task apa yang deadline hari ini?"
• "Ada berapa task yang belum selesai?"
• "Analisis produktivitas minggu ini"
• "Task mana yang overdue?"

**➕ Membuat Task Baru:**
• "Buatkan task: Review laporan keuangan"
• "Tambah task meeting client besok jam 2"
• "Buat reminder call vendor deadline 5 September"

**✅ Menyelesaikan Task:**
• "Tandai task 'Meeting pagi' selesai"
• "Complete task review document"

**✏️ Update Task:**
• "Ubah deadline task meeting jadi besok"
• "Update deskripsi task review"

**🔍 Cari Task:**
• "Cari task tentang client"
• "Ada task apa yang berisi kata 'report'?"

Tanyakan apa saja - saya akan mengakses data To-Do Anda secara real-time! 🚀"""

    try:
        # Check authentication
        from unified_auth import is_unified_authenticated
        if not is_unified_authenticated(user_id):
            return "❌ **Belum login ke Microsoft To-Do.**\n\nSilakan login terlebih dahulu dengan klik tombol '🔑 Login ke Microsoft'."

        # Get conversation memory (separated by module)
        memory_context = ""
        if memory_manager:
            try:
                memory_context = memory_manager.get_conversation_context(
                    user_id,
                    max_tokens=600,
                    module="todo"  # Separated module
                )
                if memory_context:
                    print(f"[TODO AGENT] Retrieved conversation history")
            except Exception as e:
                print(f"[TODO AGENT] Memory error: {e}")

        # Create agent
        agent = create_todo_agent(user_id)

        # Prepare input with context
        agent_input = {
            "input": query,
            "current_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Add memory context if available
        if memory_context:
            agent_input["input"] = f"""Previous conversation context:
{memory_context}

Current user query: {query}

Consider the conversation history when responding. User might reference previous discussions."""

        # Execute agent
        result = agent.invoke(agent_input)

        # Extract answer
        answer = result.get("output", "")

        # Save to memory
        if memory_manager:
            try:
                memory_manager.add_message(
                    user_id,
                    "user",
                    query,
                    module="todo"
                )
                memory_manager.add_message(
                    user_id,
                    "assistant",
                    answer,
                    metadata={
                        "type": "todo_agent",
                        "tools_used": len(result.get("intermediate_steps", []))
                    },
                    module="todo"
                )
                print(f"[TODO AGENT] Saved to separated memory")
            except Exception as e:
                print(f"[TODO AGENT] Memory save error: {e}")

        return answer

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "401" in error_msg:
            return f"❌ **Authentication Error:** {error_msg}\n\nSilakan coba login ulang."
        return f"❌ **Error:** {error_msg}\n\nCoba refresh atau login ulang jika masalah berlanjut."

# ====================
# LEGACY: Old LLM Processing (kept for backward compatibility)
# ====================

def process_todo_query_legacy(query: str, user_id: str) -> str:
    """LEGACY: Advanced LLM processing dengan better context understanding - REQUIRED user_id"""
    try:
        if not query.strip():
            return "📝 Silakan masukkan pertanyaan atau perintah terkait To-Do Anda."

        # Get current tasks data
        all_tasks = get_all_tasks(user_id)

        # Prepare detailed context
        tasks_context = prepare_detailed_context(all_tasks)
        
        # Enhanced system prompt with function calling style
        system_prompt = f"""You are a Smart Microsoft To-Do Assistant. Analyze user queries and decide appropriate actions.

Current Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User Timezone: Asia/Jakarta

{tasks_context}

Available Actions:
1. CREATE_TASK: Create new task
2. COMPLETE_TASK: Mark task as completed  
3. UPDATE_TASK: Modify existing task
4. VIEW_TASKS: Display tasks with filters

For each query, analyze intent and respond with JSON:
{{
    "intent": "create|complete|update|view",
    "confidence": 0.0-1.0,
    "action": {{
        "type": "CREATE_TASK|COMPLETE_TASK|UPDATE_TASK|VIEW_TASKS",
        "parameters": {{
            // For CREATE_TASK:
            "title": "task title",
            "description": "optional description", 
            "due_date": "YYYY-MM-DD or relative like 'today', 'tomorrow'",
            
            // For COMPLETE_TASK:
            "task_title": "exact or partial task name",
            
            // For UPDATE_TASK:
            "task_title": "task to update",
            "new_title": "new title if changing",
            "new_description": "new description if adding/changing",
            "new_due_date": "new due date if changing",
            
            // For VIEW_TASKS:
            "filters": {{
                "status": "completed|notStarted|all",
                "date_filter": "today|tomorrow|week|overdue|all",
                "show_deadlines_only": true/false
            }}
        }}
    }},
    "response_message": "Friendly Indonesian response explaining what will be done"
}}

Examples:
- "Buatkan task meeting besok" → CREATE_TASK with due_date: "tomorrow"
- "Tampilkan task hari ini" → VIEW_TASKS with date_filter: "today"
- "Selesaikan task review document" → COMPLETE_TASK with task_title: "review document"

Respond only with valid JSON."""
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        llm_response = llm.invoke(messages)

        # Parse and execute LLM response
        try:
            response_data = json.loads(llm_response.content)
            answer = execute_llm_action_advanced(response_data, all_tasks, user_id)
        except json.JSONDecodeError:
            # If LLM doesn't return valid JSON, use simple fallback
            answer = fallback_process_query(query, all_tasks, user_id)

        # Save assistant response to memory
        try:
            from internal_assistant_core import memory_manager
            if memory_manager:
                memory_manager.add_message(user_id, "assistant", answer, module="todo")
                print(f"✅ DEBUG todo_chat: Saved assistant response to memory (user_id: {user_id})")
        except ImportError:
            pass  # Memory manager not available

        return answer

    except Exception as e:
        error_msg = f"❌ *Error:* {str(e)}"
        # Save error to memory too
        try:
            from internal_assistant_core import memory_manager
            if memory_manager:
                memory_manager.add_message(user_id, "assistant", error_msg, module="todo")
        except ImportError:
            pass
        return error_msg

def prepare_detailed_context(tasks: List[Dict]) -> str:
    """Prepare detailed context untuk LLM"""
    if not tasks:
        return "User Tasks: None"
    
    context_parts = ["User Tasks Summary:"]
    current_date = datetime.now().date()
    
    # Statistics
    total = len(tasks)
    completed = len([t for t in tasks if t.get("status") == "completed"])
    pending = total - completed
    
    context_parts.append(f"- Total: {total}, Completed: {completed}, Pending: {pending}")
    
    # Today's tasks
    today_tasks = [t for t in tasks if is_task_due_today(t, current_date)]
    if today_tasks:
        context_parts.append(f"- Tasks due today: {len(today_tasks)}")
    
    # Overdue tasks
    overdue_tasks = [t for t in tasks if is_task_overdue(t, current_date)]
    if overdue_tasks:
        context_parts.append(f"- Overdue tasks: {len(overdue_tasks)}")
    
    # Recent task titles (for context and matching)
    context_parts.append("\nRecent Task Titles:")
    recent_tasks = sorted(tasks, key=lambda x: x.get('createdDateTime', ''), reverse=True)[:15]
    for task in recent_tasks:
        title = task.get('title', 'Untitled')
        status = "✅" if task.get('status') == "completed" else "⏳"
        context_parts.append(f"- {status} {title}")
    
    return "\n".join(context_parts)

def execute_llm_action_advanced(response_data: Dict, all_tasks: List[Dict], user_id: str) -> str:
    """Execute action dengan advanced LLM processing - REQUIRED user_id"""
    try:
        intent = response_data.get("intent", "view")
        action = response_data.get("action", {})
        action_type = action.get("type", "VIEW_TASKS")
        params = action.get("parameters", {})
        llm_message = response_data.get("response_message", "")

        if action_type == "CREATE_TASK":
            return execute_create_task(params, user_id, llm_message)
        elif action_type == "COMPLETE_TASK":
            return execute_complete_task(params, all_tasks, user_id, llm_message)
        elif action_type == "UPDATE_TASK":
            return execute_update_task(params, all_tasks, user_id, llm_message)
        else:
            return execute_view_tasks(params, all_tasks, llm_message)

    except Exception as e:
        return f"❌ Error executing action: {str(e)}"

def execute_create_task(params: Dict, user_id: str, llm_message: str) -> str:
    """Execute create task action - REQUIRED user_id"""
    try:
        title = params.get("title", "").strip()
        description = params.get("description", "")
        due_date_text = params.get("due_date")

        if not title:
            return "❌ Judul task tidak boleh kosong."

        # Parse due date
        due_date = None
        if due_date_text:
            due_date = parse_due_date(due_date_text)

        # Find default list
        default_list_id = find_default_list_id(user_id)

        # Create task
        created_task = create_todo_task(user_id, default_list_id, title, description, due_date)
        
        # Success response with LLM message
        response_parts = [
            llm_message if llm_message else "✅ *Task berhasil dibuat!*",
            "",
            f"📝 *Judul:* {created_task.get('title')}"
        ]
        
        if description:
            response_parts.append(f"📄 *Deskripsi:* {description}")
        
        if due_date:
            due_date_formatted = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
            response_parts.append(f"📅 *Deadline:* {due_date_formatted}")
        
        response_parts.append("")
        response_parts.append("🎯 Task berhasil ditambahkan ke Microsoft To-Do!")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error membuat task: {str(e)}"

def execute_complete_task(params: Dict, all_tasks: List[Dict], user_id: str, llm_message: str) -> str:
    """Execute complete task action - REQUIRED user_id"""
    try:
        task_title = params.get("task_title", "").strip()

        if not task_title:
            return "❌ Nama task tidak ditemukan."

        # Find task dengan LLM assistance
        target_task = find_task_with_llm(task_title, all_tasks)

        if not target_task:
            return suggest_similar_tasks(task_title, all_tasks)

        # Check if already completed
        if target_task.get("status") == "completed":
            return f"ℹ Task *'{target_task.get('title')}'* sudah selesai sebelumnya."

        # Complete task
        completed_task = complete_todo_task(user_id, target_task['list_id'], target_task['id'])
        
        response_parts = [
            llm_message if llm_message else "🎉 *Task berhasil diselesaikan!*",
            "",
            f"✅ *Task:* {completed_task.get('title')}",
            f"📋 *List:* {target_task.get('list_name', 'Tasks')}",
            f"⏰ *Diselesaikan:* {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "",
            "🎯 *Great job!* Satu task lagi selesai!"
        ]
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error menyelesaikan task: {str(e)}"

def execute_update_task(params: Dict, all_tasks: List[Dict], user_id: str, llm_message: str) -> str:
    """Execute update task action - REQUIRED user_id"""
    try:
        task_title = params.get("task_title", "").strip()

        if not task_title:
            return "❌ Nama task untuk update tidak ditemukan."

        target_task = find_task_with_llm(task_title, all_tasks)

        if not target_task:
            return suggest_similar_tasks(task_title, all_tasks)

        # Extract update parameters
        new_title = params.get("new_title")
        new_description = params.get("new_description")
        new_due_date_text = params.get("new_due_date")

        new_due_date = None
        if new_due_date_text:
            new_due_date = parse_due_date(new_due_date_text)

        # Update task
        updated_task = update_todo_task(
            user_id,
            target_task['list_id'],
            target_task['id'],
            new_title,
            new_description,
            new_due_date
        )
        
        response_parts = [
            llm_message if llm_message else "✅ *Task berhasil diupdate!*",
            "",
            f"📝 *Task:* {updated_task.get('title')}"
        ]
        
        if new_due_date:
            due_formatted = datetime.fromisoformat(new_due_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
            response_parts.append(f"📅 *Deadline Baru:* {due_formatted}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error mengupdate task: {str(e)}"

def execute_view_tasks(params: Dict, all_tasks: List[Dict], llm_message: str) -> str:
    """Execute view tasks dengan LLM-powered filtering"""
    try:
        if not all_tasks:
            return "📝 Anda belum memiliki task apapun. Coba buat task baru!"
        
        # Apply filters
        filters = params.get("filters", {})
        filtered_tasks = apply_llm_filters(all_tasks, filters)
        
        # Generate insights dengan LLM
        insights = generate_llm_insights(all_tasks, filtered_tasks, params)
        
        # Format response
        response_parts = []
        
        if llm_message:
            response_parts.append(llm_message)
            response_parts.append("")
        
        # Add task display
        response_parts.append(format_task_display(filtered_tasks))
        
        # Add insights
        if insights:
            response_parts.append("")
            response_parts.append("💡 *Insights:*")
            response_parts.append(insights)
        
        # Add summary
        total_tasks = len(all_tasks)
        filtered_count = len(filtered_tasks)
        completed_count = len([t for t in all_tasks if t.get("status") == "completed"])
        pending_count = total_tasks - completed_count
        
        response_parts.extend([
            "",
            "---",
            f"📊 *Summary:* {filtered_count} task ditampilkan dari total {total_tasks} task",
            f"✅ Selesai: {completed_count} | ⏳ Belum selesai: {pending_count}"
        ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Error menampilkan tasks: {str(e)}"

def find_task_with_llm(search_title: str, all_tasks: List[Dict]) -> Optional[Dict]:
    """Find task menggunakan LLM untuk better matching"""
    try:
        task_titles = [(task.get('title', ''), task) for task in all_tasks]
        
        if not task_titles:
            return None
        
        # Use LLM to find best match
        titles_list = [title for title, _ in task_titles]
        
        system_prompt = f"""Find the best matching task title for user search: '{search_title}'

Available task titles:
{chr(10).join([f"- {title}" for title in titles_list])}

Return only the exact title that best matches, or "NONE" if no good match exists.
Consider partial matches, typos, and semantic similarity."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Find best match for: {search_title}")
        ]
        
        llm_response = llm.invoke(messages)
        matched_title = llm_response.content.strip()
        
        if matched_title == "NONE":
            return None
        
        # Find task object by matched title
        for title, task in task_titles:
            if title.lower() == matched_title.lower():
                return task
        
        # Fallback to original fuzzy matching
        return find_task_by_title(all_tasks, search_title)
        
    except Exception:
        # Fallback to original method
        return find_task_by_title(all_tasks, search_title)

def generate_llm_insights(all_tasks: List[Dict], filtered_tasks: List[Dict], query_params: Dict) -> str:
    """Generate insights menggunakan LLM"""
    try:
        current_date = datetime.now().date()
        
        # Prepare statistics
        stats = {
            "total_tasks": len(all_tasks),
            "completed_tasks": len([t for t in all_tasks if t.get("status") == "completed"]),
            "pending_tasks": len([t for t in all_tasks if t.get("status") != "completed"]),
            "today_tasks": len([t for t in all_tasks if is_task_due_today(t, current_date)]),
            "overdue_tasks": len([t for t in all_tasks if is_task_overdue(t, current_date)]),
            "filtered_count": len(filtered_tasks)
        }
        
        system_prompt = f"""Generate helpful insights about user's task management based on these statistics:

{json.dumps(stats, indent=2)}

Current date: {current_date}

Provide 1-2 brief, actionable insights in Indonesian. Focus on:
- Productivity patterns
- Urgent items needing attention  
- Motivational observations
- Practical suggestions

Keep insights short and engaging. Use emojis appropriately."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Generate insights for these task statistics")
        ]
        
        llm_response = llm.invoke(messages)
        return llm_response.content.strip()
        
    except Exception:
        # Simple fallback insights
        if stats.get("overdue_tasks", 0) > 0:
            return f"⚠ Anda memiliki {stats['overdue_tasks']} task yang overdue. Prioritaskan untuk diselesaikan!"
        elif stats.get("today_tasks", 0) > 0:
            return f"📅 Ada {stats['today_tasks']} task dengan deadline hari ini. Semangat!"
        else:
            return "🎯 Terus pertahankan momentum dalam menyelesaikan tasks!"