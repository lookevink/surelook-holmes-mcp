# Surelook Holmes MCP Server

A Model Context Protocol (MCP) server for Surelook Holmes, built with `fastmcp` and using SSE (Server-Sent Events) transport.

## Prerequisites

- Python 3.10+ (We recommend 3.12)
- `uv` (optional, but recommended for dependency management)

## Setup

1. **Create Virtual Environment**
     
   Using `uv` (recommended):
   ```bash
   uv venv --python 3.12 .venv
   ```
   
   Or using standard `python`:
   ```bash
   python3 -m venv .venv
   ```

2. **Install Dependencies**

   ```bash
   uv pip install -p .venv fastmcp supabase python-dotenv
   # OR
   source .venv/bin/activate
   pip install fastmcp supabase python-dotenv
   ```

3. **Configure Environment Variables**

   Create a `.env` file in the project root:
   ```env
   PUBLIC_SUPABASE_URL=your_project_url
   PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=your_public_key
   RAPIDAPI_KEY=your_rapidapi_key
   ```

## Running the Server

Run the server using the configured transport (SSE):

```bash
.venv/bin/python mcp_server.py
```

By default, this will start the server on http://127.0.0.1:8000 (or similar default port provided by fastmcp).

## Features

- **Tools**:
  - `add(a, b)`: Adds two numbers.
- **Resources**:
  - `greeting://{name}`: specific greeting resource.

## Transport

This server uses `sse` transport (Streamable HTTP).
