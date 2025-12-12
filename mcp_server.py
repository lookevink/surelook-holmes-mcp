import os
import warnings
import platform
import sys
import requests

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

# GET RAPIDAPI_KEY from environment
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Create an MCP server
mcp = FastMCP("Surelook Holmes")

@mcp.tool()
def get_identity(identity_id: str) -> Dict[str, Any]:
    """Get a specific identity by ID."""
    if not supabase:
        return {"error": "Supabase client not initialized"}
    
    response = supabase.table("identities").select("*").eq("id", identity_id).single().execute()
    return response.data

@mcp.tool()
def update_identity(
    identity_id: str,
    name: Optional[str] = None,
    relationship_status: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update an identity.
    
    Args:
        identity_id: The UUID of the identity to update.
        name: New name (optional).
        relationship_status: New relationship status (optional).
        linkedin_url: New LinkedIn URL (optional).
        metadata: New metadata dictionary (optional, merges or replaces depending on supabase behavior, usually replaces top level keys).
    """
    if not supabase:
        return {"error": "Supabase client not initialized"}
    
    updates = {}
    if name is not None:
        updates["name"] = name
    if relationship_status is not None:
        updates["relationship_status"] = relationship_status
    if linkedin_url is not None:
        updates["linkedin_url"] = linkedin_url
    if metadata is not None:
        updates["metadata"] = metadata
        
    if not updates:
        return {"error": "No updates provided"}
        
    response = supabase.table("identities").update(updates).eq("id", identity_id).execute()
    return response.data[0] if response.data else {}

@mcp.tool()
def get_events(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get events associated with a specific session ID."""
    if not supabase:
        return [{"error": "Supabase client not initialized"}]
    
    response = supabase.table("events").select("*").eq("session_id", session_id).order("created_at").limit(limit).execute()
    return response.data

@mcp.tool()
def create_event(
    type: str,
    content: str,
    session_id: Optional[str] = None,
    related_identity_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new event.
    
    Args:
        type: Must be one of 'VISUAL_OBSERVATION', 'CONVERSATION_NOTE', 'AGENT_WHISPER'.
        content: The content of the event.
        session_id: Optional UUID of the associated session.
        related_identity_id: Optional UUID of the related identity.
    """
    if not supabase:
        return {"error": "Supabase client not initialized"}
    
    data = {
        "type": type,
        "content": content,
    }
    if session_id:
        data["session_id"] = session_id
    if related_identity_id:
        data["related_identity_id"] = related_identity_id
        
    response = supabase.table("events").insert(data).execute()
    return response.data[0] if response.data else {}


@mcp.tool()
def get_notes(identity_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get conversation notes (events with type 'CONVERSATION_NOTE') for a specific identity.
    
    Args:
        identity_id: The UUID of the identity.
    """
    if not supabase:
        return [{"error": "Supabase client not initialized"}]
    
    response = supabase.table("events").select("*").eq("related_identity_id", identity_id).eq("type", "NOTES").order("created_at", desc=True).limit(limit).execute()
    return response.data

@mcp.tool()
def who_is_this(linkedin_url: str) -> Dict[str, Any]:
    """
    Identify a person from their LinkedIn URL and get their latest post.
    
    Args:
        linkedin_url: The full LinkedIn profile URL.
    """
    if not RAPIDAPI_KEY:
        return {"error": "RAPIDAPI_KEY not set in environment"}

    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/enrich-lead"
    querystring = {
        "linkedin_url": linkedin_url,
        "include_skills": "false",
        "include_certifications": "false", 
        "include_publications": "false",
        "include_honors": "false",
        "include_volunteers": "false",
        "include_projects": "false",
        "include_patents": "false",
        "include_courses": "false",
        "include_organizations": "false",
        "include_profile_status": "false",
        "include_company_public_url": "false"
    }

    headers = {
        "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        # Check if wrapped in 'data' field (as seen in sample)
        profile = data.get("data", data)
        
        # 1. Name
        name = profile.get("full_name") or f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
        
        # 2. Company
        # Look for current experience
        current_company = "Unknown"
        experiences = profile.get("experiences", [])
        if experiences and isinstance(experiences, list):
            # Sort by start date if possible, or just find first current
            # Sample has is_current boolean
            current_role = next((exp for exp in experiences if exp.get("is_current")), None)
            if not current_role and experiences:
                # If no current, take the first one (most recent usually)
                current_role = experiences[0]
            
            if current_role:
                comp = current_role.get("company", "")
                title = current_role.get("title", "")
                current_company = f"{title} at {comp}" if title and comp else comp or title
            
        return {
            "name": name,
            "company": current_company,
            "about": profile.get("about") # Extra context often helpful
        }

    except Exception as e:
        return {"error": f"Failed to fetch LinkedIn data: {str(e)}"}


@mcp.resource("system://info")
def system_info() -> str:
   """
   Returns basic system information including Python version and platform.
   """
   return f"""
   System Information:
   ------------------
   Platform: {platform.system()} {platform.release()}
   Python Version: {sys.version}
   """


if __name__ == "__main__":
    # Run the server with Streamable-HTTP transport (streamable-http)
    print("Starting Surelook Holmes MCP server on Streamable-HTTP transport...")
    mcp.run(transport="streamable-http")
