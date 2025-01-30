# middlewares/json_handler.py
from fastapi import Request
import json


async def raw_json_middleware(request: Request, call_next):
    """Handles raw JSON data for middleware"""
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.body()
            if body:
                raw_json = body.decode()
                modified_body = process_raw_json(raw_json)
                if modified_body:
                    request._receive = create_receive_function(modified_body)
        except Exception as error:
            print(f"Middleware error: {str(error)}")

    response = await call_next(request)
    return response


def process_raw_json(raw_str: str) -> str:
    """Processes raw JSON string to handle potential errors"""
    try:
        json.loads(raw_str)
        return None  # No changes needed if JSON is already valid
    except json.JSONDecodeError:
        processed_str = raw_str.replace('""', r'\"')
        return handle_quotes_in_string(processed_str)


def handle_quotes_in_string(raw_str: str) -> str:
    """Handles quotes within a JSON string"""
    in_single_quotes = False
    final_processed = []
    for char in raw_str:
        if char == "'":
            in_single_quotes = not in_single_quotes
        elif char == '"' and in_single_quotes:
            final_processed.append(r'\"')
            continue
        final_processed.append(char)
    return "".join(final_processed)


def create_receive_function(processed_body: str):
    """Creates a custom `receive` function with processed body"""

    async def receive():
        return {
            "type": "http.request",
            "body": processed_body.encode()
        }

    return receive
