import sys
import json
import mcp_helper

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")
            
            if method is None:
                continue
            
            # Notifications do not have an id and don't need a response
            if req_id is None or (isinstance(method, str) and method.startswith("notifications/")):
                continue
            
            # Handle standard requests
            res = mcp_helper.handle_request(method, req.get("params", {}))
            
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": res
            }
            print(json.dumps(response), flush=True)
            
        except Exception as e:
            if 'req_id' in locals() and req_id is not None:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(response), flush=True)

if __name__ == "__main__":
    main()