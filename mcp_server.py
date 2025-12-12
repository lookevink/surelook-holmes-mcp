import os
import warnings

# Suppress Pydantic deprecation warnings from dependencies
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince20.*")
from typing import List, Optional, Dict, Any
from fastmcp import FastMCP
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL and SUPABASE_KEY (or PUBLIC variants) environment variables must be set.")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    supabase = None

# Create an MCP server
mcp = FastMCP("Surelook Holmes")

@mcp.tool()
def list_sessions(limit: int = 10) -> List[Dict[str, Any]]:
    """List recent sessions from the database."""
    if not supabase:
        return [{"error": "Supabase client not initialized"}]
    
    response = supabase.table("sessions").select("*").order("created_at", desc=True).limit(limit).execute()
    return response.data

@mcp.tool()
def get_session(session_id: str) -> Dict[str, Any]:
    """Get a specific session by ID."""
    if not supabase:
        return {"error": "Supabase client not initialized"}
    
    response = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
    return response.data

@mcp.tool()
def list_identities(limit: int = 10) -> List[Dict[str, Any]]:
    """List identities from the database."""
    if not supabase:
        return [{"error": "Supabase client not initialized"}]
    
    response = supabase.table("identities").select("*").limit(limit).execute()
    return response.data

@mcp.tool()
def get_events(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get events associated with a specific session ID."""
    if not supabase:
        return [{"error": "Supabase client not initialized"}]
    
    response = supabase.table("events").select("*").eq("session_id", session_id).order("created_at").limit(limit).execute()
    return response.data

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a greeting for a name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    # Run the server with SSE transport (streamable-http)
    print("Starting Surelook Holmes MCP server on SSE transport...")
    mcp.run(transport="streamable-http")
