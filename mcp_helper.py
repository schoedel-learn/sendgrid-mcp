from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import os
import json
import datetime
import requests
from datetime import datetime
import base64 
import pandas as pd

# =============================================================================
# Variables
# =============================================================================

# Sendgrid Key as env variable
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
sg = SendGridAPIClient(SENDGRID_API_KEY)

# =============================================================================
# MCP Protocol Request Routing
# =============================================================================

def handle_request(method, params):
    """
    Main request router for MCP (Model Context Protocol) JSON-RPC methods.
    Supported:
      - initialize
      - tools/list
      - tools/call
    Notifications (notifications/*) are handled in app.py (204 No Content).
    """
    if method == "initialize":
        return handle_initialize()
    elif method == "tools/list":
        return handle_tools_list()
    elif method == "tools/call":
        return handle_tool_call(params)
    else:
        # Let app.py wrap unknown methods into a proper JSON-RPC error
        raise ValueError(f"Method not found: {method}")


# =============================================================================
# MCP Protocol Handlers
# =============================================================================

def handle_initialize():
    """
    JSON-RPC initialize response.
    Keep protocolVersion consistent with your current implementation.
    """
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "sendgrid_mcp",
            "version": "0.1.0"
        },
        "capabilities": {
            "tools": {}
        }
    }


def handle_tools_list():
    """
    JSON-RPC tools/list result.
    IMPORTANT: For JSON-RPC MCP, schema field is camelCase: inputSchema
    """
    return {
        "tools": [
            {
                "name": "list_email_templates",
                "description": "fetches a list of email templates from the SendGrid API",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "list_type": {
                            "type": "string",
                            "description": "the type of list to fetch - dynamic or legacy. Default to dynamic if not specified."
                        }
                    },
                    "required": ["list_type"],
                    "additionalProperties": False
                }
            },
            {
                "name": "get_html_template_by_id",
                "description": "fetches the html for a sendgrid email template by id",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "the id of the sendgrid email template to fetch the html for"
                        }
                    },
                    "required": ["template_id"],
                    "additionalProperties": False
                }   
            },
            {
                "name": "save_email_html_template",
                "description": "Saves a html email template to sendgrid.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "The id of the sendgrid email template to save. Either formatted starting with d-, or is TBD."
                        },
                        "template_name": {
                            "type": "string",
                            "description": "The name of the sendgrid email template to save. "
                        },
                        "template_html": {
                            "type": "string",
                            "description": "The html for a sendgrid email template. The template must feature inline css styling to ensure capability. "
                        },
                        
                    },
                    "required": ["template_id", "template_name", "template_html"],
                    "additionalProperties": False
                }   
            },
            {
                "name": "get_aggregate_email_stats",
                "description": "fetches the aggregate email stats (such as delivered, opens, bounces, clicks, etc.) for a sendgrid customer aggregated by day, week or month. This is useful for understanding the overall performance of a company's email program.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "the start date of the period to fetch the stats for in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "the end date of the period to fetch the stats for in YYYY-MM-DD format"
                        },
                        "aggregated_by": {
                            "type": "string",
                            "description": "the type of aggregation to use - day, week or month. Default to day if not specified."
                        }
                    },
                    "required": ["start_date", "end_date", "aggregated_by"],
                    "additionalProperties": False
                }   
            },
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
        ]
    }



def handle_tool_call(params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    # Decode string args if needed
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except Exception:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "Invalid arguments: expected object or JSON string."}]
            }

    if tool_name == "list_email_templates":
        data = list_email_templates(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}

    elif tool_name == "get_html_template_by_id":
        data = get_html_template_by_id(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}

    elif tool_name == "get_aggregate_email_stats":
        data = get_aggregate_email_stats(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}

    elif tool_name == "save_email_html_template":
        data = save_email_html_template(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}


    elif tool_name == "authenticate_domain":
        data = authenticate_domain(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}

    elif tool_name == "verify_domain_authentication":
        data = verify_domain_authentication(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}
    else:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Tool not found: {tool_name}"}]
        }




# =============================================================================
# SendGrid Functions
# =============================================================================

def list_email_templates(arguments):
    """
    Fetches a list of email templates from the SendGrid API
    """

    # Extract chat summary from arguments
    list_type = arguments.get('list_type')

    url = f"https://api.sendgrid.com/v3/templates?generations={list_type}"
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    print(response.text)

    if response.status_code != 200:
        print(f"Failed to fetch templates: {response.text}")
        return

    data = response.json()
    templates = data.get("templates", [])

    if not templates:
        print("No dynamic templates found.")
        return                    

    return templates


def get_html_template_by_id(arguments):

    """
    Fetches the html for a sendgrid email template by id
    
    """

    template_id = arguments.get('template_id')

    sg = SendGridAPIClient(SENDGRID_API_KEY)

    response = sg.client.templates._(template_id).get()

    response_obj = json.loads(response.body.decode('utf-8'))

    version_len = len(response_obj['versions']) - 1

    return response_obj['versions'][version_len]['html_content']


def get_aggregate_email_stats(arguments):
    """
    Fetches the aggregate email stats (such as delivered, opens, bounces, clicks, etc.) for a sendgrid customer aggregated by day, week or month. This is useful for understanding the overall performance of a company's email program.
    """

    start_date = arguments.get('start_date')
    end_date = arguments.get('end_date')
    aggregated_by = arguments.get('aggregated_by')

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "aggregated_by": aggregated_by
    }

    response = sg.client.stats.get(query_params=params)

    response_obj = json.loads(response.body.decode('utf-8'))

    formatted_response = format_email_stats(response_obj, str(params))

    return formatted_response


def format_email_stats(response_obj, query):

    """
    Formats the email stats response in an LLM friendly format to be sent to the requesting agent.
    

    Args:
        response_obj (dict): The response object from the SendGrid API
        query (string): The user's api query payload object as a string
        Example response object:
        [{'date': '2025-10-01', 'stats': [{'metrics': {'blocks': 0, 'bounce_drops': 0, 'bounces': 0, 'clicks': 0, 'deferred': 0, 'delivered': 10, 'invalid_emails': 0, 'opens': 13, 'processed': 10, 'requests': 10, 'spam_report_drops': 0, 'spam_reports': 0, 'unique_clicks': 0, 'unique_opens': 11, 'unsubscribe_drops': 0, 'unsubscribes': 0}}]}]

    Returns:
        formatted_output (string): The formatted output for the requesting agent
    """

    # Get the current timestamp for when the query was requested
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_cleaned = []

    for d in response_obj:
        data_cleaned.append({
            "date": d["date"],
            "delivered": d["stats"][0]["metrics"]["delivered"],
            "opens": d["stats"][0]["metrics"]["opens"],
            "clicks": d["stats"][0]["metrics"]["clicks"],
            "bounces": d["stats"][0]["metrics"]["bounces"],
            "unsubscribes": d["stats"][0]["metrics"]["unsubscribes"]
        })

    # Calculate totals and averages using pandas
    df = pd.DataFrame(data_cleaned)
    total_delivered = df["delivered"].sum()
    total_opens = df["opens"].sum()
    total_clicks = df["clicks"].sum()
    total_bounces = df["bounces"].sum()
    total_unsubscribes = df["unsubscribes"].sum()

    avg_ctr = (total_clicks / total_opens) * 100
    avg_bounces = (total_bounces / total_delivered) * 100
    avg_unsubscribes = (total_unsubscribes / total_delivered) * 100

    # Build summary section
    summary_section = (
        f"Summary of metrics across selected period:\n"
        f"  - Total Delivered: {total_delivered}\n"
        f"  - Total Opens: {total_opens}\n"
        f"  - Total Clicks: {total_clicks}\n"
        f"  - Total Bounces: {total_bounces}\n"
        f"  - Total Unsubscribes: {total_unsubscribes}\n"
        f"  - Average CTR: {avg_ctr:.2f}%\n"
        f"  - Bounce Rate: {avg_bounces:.2f}%\n"
        f"  - Unsubscribe Rate: {avg_unsubscribes:.2f}%\n"
    )

    # Create the data table section
    table_header = "Date | Delivered | Opens | Clicks | Bounces | Unsubscribes"
    table_divider = "-" * len(table_header)

    table_rows = []
    for stat in data_cleaned:
        date = stat["date"]
        delivered = stat["delivered"]
        opens = stat["opens"]
        clicks = stat["clicks"]
        bounces = stat["bounces"]
        unsubscribes = stat["unsubscribes"]
        table_rows.append(f"{date} | {delivered} | {opens} | {clicks} | {bounces} | {unsubscribes}")

    table_body = "\n".join(table_rows)

    # Compose final formatted report
    formatted_output = f"""
### SendGrid Email Stats ###

This data set helps businesses understand the performance of their email program. 

The following query has been requested by the user on {timestamp}. The API payload object used to fetch this data is as follows:    
{query}

Please review this data in detail and finalize the user's request with an analysis of the facts presented below:

{summary_section}

{table_header}
{table_divider}
{table_body}

"""
    return formatted_output



def create_dynamic_template(template_name):

    SENDGRID_TEMPLATE_URL = "https://api.sendgrid.com/v3/templates"

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "name": template_name,
        "generation": "dynamic"
    }

    response = requests.post(SENDGRID_TEMPLATE_URL, headers=headers, json=data)

    if response.status_code != 201:
        print("Error creating template shell:", response.text)
        return None

    template_id = response.json()["id"]
    print(f"Dynamic Template created successfully with ID: {template_id}")
    return template_id


def add_template_version(new_template_id, template_html, template_name):

    SENDGRID_TEMPLATE_URL = "https://api.sendgrid.com/v3/templates"
    version_url = f"{SENDGRID_TEMPLATE_URL}/{new_template_id}/versions"

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    # editor can be code or design
    version_data = {
        "active": 1,
        "name": template_name,
        "subject": "",
        "html_content": template_html,
        "plain_content": "",
        "generate_plain_content": True,
        "editor": "code"
    }

    response = requests.post(version_url, headers=headers, json=version_data)
    if response.status_code != 201:
        print("Error adding dynamic version:", response.text)
    else:
        print("Dynamic version added successfully!")
        return 'template saved'



def save_email_html_template(arguments):

    """
    Saves a new html for a sendgrid email template by id
    
    """
    try:
        template_id = arguments.get('template_id')
        template_name = arguments.get('template_name')
        template_html = arguments.get('template_html')

        # Step 1 - create a dynamic template id
        new_template_id = create_dynamic_template(template_name)

        # Step 2 - add the first version to the template
        save_msg = add_template_version(new_template_id, template_html, template_name)

        return new_template_id

    except Exception as e:

        print(f"Error creating template: {e}")









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
