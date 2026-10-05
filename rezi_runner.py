import asyncio
import json
import os
import argparse
from datetime import datetime
from mcp.client.sse import sse_client
from mcp import ClientSession

# Rezi's official MCP endpoint
REZI_MCP_URL = "https://api.rezi.ai/mcp"

async def run_rezi_tool(tool_name: str, tool_args: dict):
    token = os.environ.get("REZI_ACCESS_TOKEN")
    if not token:
        raise ValueError("REZI_ACCESS_TOKEN is missing. Set it in GitHub Secrets.")

    headers = {"Authorization": f"Bearer {token}"}

    # Use sse_client for remote HTTP connections instead of streamable_http
    async with sse_client(REZI_MCP_URL, headers=headers) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Execute the requested Rezi tool
            result = await session.call_tool(tool_name, arguments=tool_args)
            return result

def save_json_output(tool_name: str, data):
    output_dir = "mcp_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{tool_name}_{timestamp}.json")
    
    # Extract data securely depending on MCP SDK response format
    output_data = {
        "tool": tool_name,
        "result": data.model_dump() if hasattr(data, 'model_dump') else str(data)
    }
    
    with open(filepath, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Output saved to {filepath}")

async def main():
    parser = argparse.ArgumentParser(description="Run Rezi MCP Tools On-Demand")
    parser.add_argument("--tool", required=True, help="Rezi tool to execute")
    parser.add_argument("--kwargs", default="{}", help="JSON string of arguments")
    
    args = parser.parse_args()
    tool_args = json.loads(args.kwargs)

    result = await run_rezi_tool(args.tool, tool_args)
    save_json_output(args.tool, result)

if __name__ == "__main__":
    asyncio.run(main())