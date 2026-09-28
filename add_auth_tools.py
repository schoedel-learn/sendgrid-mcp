import json

def update_file():
    with open('mcp_helper.py', 'r') as f:
        content = f.read()
    
    tools_list_addition = """
            {
                "name": "authenticate_domain",
                "description": "Authenticates a new domain for SendGrid email sending (Domain Authentication). Returns the DNS CNAME records that need to be added to the domain's DNS provider.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "The domain name to authenticate (e.g. schoedel.design.ai)"
                        }
                    },
                    "required": ["domain"],
                    "additionalProperties": False
                }
            },
            {
                "name": "verify_domain_authentication",
                "description": "Validates the DNS records for a domain authentication after they have been added to the DNS provider.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain_id": {
                            "type": "integer",
                            "description": "The ID of the authenticated domain returned by authenticate_domain"
                        }
                    },
                    "required": ["domain_id"],
                    "additionalProperties": False
                }
            }
"""
    
    # insert before the closing bracket of tools list
    content = content.replace('            }\n        ]\n    }', '            },' + tools_list_addition + '        ]\n    }')
    
    tool_call_addition = """
    elif tool_name == "authenticate_domain":
        data = authenticate_domain(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}

    elif tool_name == "verify_domain_authentication":
        data = verify_domain_authentication(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}
"""

    content = content.replace('    else:\n        return {', tool_call_addition + '    else:\n        return {')
    
    sendgrid_functions = """
def authenticate_domain(arguments):
    domain = arguments.get('domain')
    url = "https://api.sendgrid.com/v3/whitelabel/domains"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "domain": domain,
        "automatic_security": True
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code not in (200, 201):
        return f"Error authenticating domain: {response.text}"
    return response.json()

def verify_domain_authentication(arguments):
    domain_id = arguments.get('domain_id')
    url = f"https://api.sendgrid.com/v3/whitelabel/domains/{domain_id}/validate"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    if response.status_code not in (200, 201):
        return f"Error validating domain: {response.text}"
    return response.json()
"""
    
    content = content + sendgrid_functions
    
    with open('mcp_helper.py', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    update_file()
