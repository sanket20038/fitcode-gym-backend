# api/index.py

from src.main import app as flask_app

def handler(request, context):
    # Convert the incoming request to WSGI environment
    environ = request.environ

    # Define a dummy start_response function
    def start_response(status, response_headers, exc_info=None):
        return None

    # Get the response from the Flask app
    response = flask_app(environ, start_response)

    # Read the response body
    body = b"".join(response)

    # Return response compatible with Vercel
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": body.decode()
    }
