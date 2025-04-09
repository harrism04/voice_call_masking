from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import json
import logging
import signal
import sys
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logs go to Docker logs
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware for ngrok
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
VOICE_API_BASE_URL = os.getenv("VOICE_API_BASE_URL", "https://voice.wavecell.com/api/v1")
PORT = int(os.getenv("PORT", "5678"))

# Global state for health checks and call tracking
health_status: Dict[str, str] = {"status": "starting"}
active_calls: Dict[str, Dict] = {}  # Track call sessions

# Graceful shutdown handler
def handle_shutdown(signum, frame):
    logger.info("Received shutdown signal, cleaning up...")
    health_status["status"] = "shutting_down"
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Initialize skip_logging attribute
    request.state.skip_logging = False

    # Skip logging for health check requests to reduce noise
    if request.url.path == "/health":
        request.state.skip_logging = True

    # Only log if not a health check
    if not request.state.skip_logging:
        logger.info(f"Incoming request: {request.method} {request.url}")

    response = await call_next(request)

    # Only log if not a health check
    if not request.state.skip_logging:
        logger.info(f"Response status: {response.status_code}")

    return response

@app.post("/api/webhooks/vca")
async def voice_call_action(request: Request):
    """Handle Voice Call Action (VCA) webhooks from 8x8"""
    try:
        # Log raw request details
        logger.info(f"VCA Webhook received - Method: {request.method}")
        logger.info(f"VCA Webhook URL: {request.url}")
        logger.info(f"VCA Headers: {dict(request.headers)}")

        raw_body = await request.body()
        logger.info(f"VCA Raw body: {raw_body}")

        raw_json = json.loads(raw_body)
        logger.info(f"Received Voice Call Action webhook: {raw_json}")

        # Extract data from VCA webhook
        payload = raw_json.get("payload", {})
        event_type = raw_json.get("eventType")
        call_status = payload.get("callStatus")
        session_id = payload.get("sessionId")
        incoming_number = payload.get("source")
        virtual_number = payload.get("destination")

        logger.info(f"Extracted fields - event_type: {event_type}, call_status: {call_status}, session_id: {session_id}")

        # Only process new inbound calls
        if event_type != "CALL_ACTION" or call_status != "CALL_RECEIVED" or not session_id:
            logger.info(f"Ignoring non-inbound call event: {event_type} - {call_status}")
            return JSONResponse(content={"status": "ignored"})

        # Get credentials and configuration
        api_key = os.getenv("EIGHT_X_EIGHT_API_KEY")
        subaccount_id = os.getenv("EIGHT_X_EIGHT_SUBACCOUNT_ID")
        forwarded_number = os.getenv("FORWARDED_PHONE_NUMBER")

        if not all([api_key, subaccount_id, forwarded_number, virtual_number]):
            missing = []
            if not api_key: missing.append("EIGHT_X_EIGHT_API_KEY")
            if not subaccount_id: missing.append("EIGHT_X_EIGHT_SUBACCOUNT_ID")
            if not forwarded_number: missing.append("FORWARDED_PHONE_NUMBER")
            if not virtual_number: missing.append("virtual_number from webhook")
            error_msg = f"Missing required configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Store call context
        active_calls[session_id] = {
            "caller": incoming_number,
            "virtual_number": virtual_number,
            "forwarded_number": forwarded_number,
            "status": "bridging",
            "call_id": payload.get("callId")
        }
        logger.info(f"Stored call context for session {session_id}: {active_calls[session_id]}")

        # Strip '+' from phone numbers
        virtual_number = virtual_number.lstrip('+')
        forwarded_number = forwarded_number.lstrip('+')

        # Prepare and return the call masking callflow response
        response_body = {
            "callflow": [
                {
                    "action": "makeCall",
                    "params": {
                        "source": virtual_number,
                        "destination": forwarded_number
                    }
                }
            ]
        }
        logger.info(f"Returning VCA response with callflow: {response_body}")

        return JSONResponse(
            status_code=200,
            content=response_body
        )

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in webhook payload: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={"error": error_msg}
        )
    except Exception as e:
        error_msg = f"Error processing VCA webhook: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@app.post("/api/webhooks/vcs")
async def voice_call_status(request: Request):
    """Handle Voice Call Status (VCS) webhooks from 8x8"""
    raw_body = await request.body()
    raw_json = json.loads(raw_body)
    logger.info(f"Received Voice Call Status webhook: {raw_json}")

    try:
        # Return 200 OK immediately to acknowledge receipt
        if not raw_json or "eventType" not in raw_json:
            logger.warning("Invalid VCS webhook payload")
            return JSONResponse(content={"status": "ok"}, status_code=200)

        # Process webhook asynchronously after responding
        payload = raw_json.get("payload", {})
        event_type = raw_json.get("eventType")
        call_status = payload.get("callStatus")
        session_id = payload.get("sessionId")
        call_id = payload.get("callId")

        # Update call tracking if we have the session
        if session_id and session_id in active_calls:
            active_calls[session_id].update({
                "status": call_status,
                "event_type": event_type,
                "call_id": call_id,
                "last_update": payload
            })
            logger.info(f"Call {call_id} status: {call_status} for session {session_id}")

        return JSONResponse(content={"status": "ok"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing Voice Call Status webhook: {str(e)}")
        # Still return 200 OK to acknowledge receipt
        return JSONResponse(content={"status": "ok"}, status_code=200)

@app.post("/api/webhooks/vss")
async def voice_session_status(request: Request):
    """Handle Voice Session Status (VSS) webhooks from 8x8"""
    raw_body = await request.body()
    raw_json = json.loads(raw_body)
    logger.info(f"Received Voice Session Status webhook: {raw_json}")

    try:
        # Return 200 OK immediately to acknowledge receipt
        if not raw_json or "eventType" not in raw_json:
            logger.warning("Invalid VSS webhook payload")
            return JSONResponse(content={"status": "ok"}, status_code=200)

        # Process webhook asynchronously after responding
        payload = raw_json.get("payload", {})
        event_type = raw_json.get("eventType")
        session_id = payload.get("sessionId")

        # Update session tracking if we have the session
        if session_id and session_id in active_calls:
            active_calls[session_id].update({
                "session_status": payload.get("sessionStatus"),
                "event_type": event_type,
                "last_vss_update": payload
            })
            logger.info(f"Session {session_id} status updated: {payload.get('sessionStatus')}")

        return JSONResponse(content={"status": "ok"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing Voice Session Status webhook: {str(e)}")
        # Still return 200 OK to acknowledge receipt
        return JSONResponse(content={"status": "ok"}, status_code=200)

@app.get("/health")
async def health_check(request: Request):
    """Enhanced health check endpoint for Docker healthcheck

    Reduced logging for health checks to minimize log noise.
    Only logs on status changes or errors.
    """
    # Skip logging for health check requests
    request.state.skip_logging = True

    try:
        # Check if required environment variables are set
        required_vars = ["EIGHT_X_EIGHT_API_KEY", "EIGHT_X_EIGHT_SUBACCOUNT_ID", "FORWARDED_PHONE_NUMBER"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            # Only log if status changed from previous state
            if health_status.get("status") != "misconfigured":
                logger.warning(f"Health check failed: Missing environment variables {missing_vars}")

            health_status["status"] = "misconfigured"
            health_status["missing_vars"] = missing_vars
            return JSONResponse(
                status_code=503,
                content=health_status
            )

        # Only log if status changed from previous state
        if health_status.get("status") != "healthy":
            logger.info("Health check status changed to healthy")

        health_status["status"] = "healthy"
        return health_status

    except Exception as e:
        # Always log exceptions
        logger.error(f"Health check error: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return JSONResponse(
            status_code=503,
            content=health_status
        )

@app.on_event("startup")
async def startup_event():
    logger.info(f"Server starting up")
    # 8x8 API details
    api_key = os.getenv("EIGHT_X_EIGHT_API_KEY")
    subaccount_id = os.getenv("EIGHT_X_EIGHT_SUBACCOUNT_ID")
    forwarded_phone = os.getenv("FORWARDED_PHONE_NUMBER")

    # Validate all required credentials
    missing_vars = []
    if not api_key:
        missing_vars.append("EIGHT_X_EIGHT_API_KEY")
    if not subaccount_id:
        missing_vars.append("EIGHT_X_EIGHT_SUBACCOUNT_ID")
    if not forwarded_phone:
        missing_vars.append("FORWARDED_PHONE_NUMBER")

    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    health_status["status"] = "healthy"

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown handler to ensure proper cleanup"""
    logger.info("Shutting down Call Masking Server...")
    health_status["status"] = "shutdown"

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_config=None  # Use our logging config
    )