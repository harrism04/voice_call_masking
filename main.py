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
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/api/webhooks/mask")
async def mask_call(request: Request):
    # Get raw webhook data
    raw_body = await request.body()
    raw_json = json.loads(raw_body)
    logger.info(f"Received call masking webhook: {raw_json}")
    
    try:
        # Extract data from VCA webhook
        payload = raw_json.get("payload", {})
        event_type = raw_json.get("eventType")
        call_status = payload.get("callStatus")
        session_id = payload.get("sessionId")
        incoming_number = payload.get("source")
        virtual_number = payload.get("destination")  # Our virtual number

        # Only process new inbound calls
        if event_type != "CALL_ACTION" or call_status != "CALL_RECEIVED" or not session_id:
            return JSONResponse(content={"status": "ignored"})

        # Get credentials and configuration
        api_key = os.getenv("EIGHT_X_EIGHT_API_KEY")
        subaccount_id = os.getenv("EIGHT_X_EIGHT_SUBACCOUNT_ID")
        forwarded_number = os.getenv("FORWARDED_PHONE_NUMBER")

        if not all([api_key, subaccount_id, forwarded_number, virtual_number]):
            raise ValueError("Missing required configuration")

        # Store call context
        active_calls[session_id] = {
            "caller": incoming_number,
            "virtual_number": virtual_number,
            "forwarded_number": forwarded_number,
            "status": "bridging"
        }

        # Strip '+' from phone numbers
        virtual_number = virtual_number.lstrip('+')
        forwarded_number = forwarded_number.lstrip('+')

        # Prepare the call masking request - use virtual number as source
        request_body = {
            "clientActionId": f"mask_{session_id}",
            "callflow": [
                {
                    "action": "say",
                    "params": {
                        "text": "Please wait while we connect your call.",
                        "voiceProfile": "en-US-BenjaminRUS",
                        "repetition": 1,
                        "speed": 1
                    }
                },
                {
                    "action": "makeCall",
                    "params": {
                        "source": virtual_number,  # Use our virtual number as source
                        "destination": forwarded_number
                    }
                }
            ]
        }
        
        # Make API call to initiate masked call
        api_url = f"{VOICE_API_BASE_URL}/subaccounts/{subaccount_id}/callflows"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            logger.info(f"Call Masking API Response: {response.status_code}")
            if response.status_code >= 400:
                raise ValueError(f"Call Masking API error: {response.text}")
                
            return JSONResponse(content={"status": "bridging_initiated", "sessionId": session_id})
            
    except Exception as e:
        logger.error(f"Error masking call: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
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

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint for Docker healthcheck"""
    try:
        # Check if required environment variables are set
        required_vars = ["EIGHT_X_EIGHT_API_KEY", "EIGHT_X_EIGHT_SUBACCOUNT_ID", "FORWARDED_PHONE_NUMBER"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            health_status["status"] = "misconfigured"
            health_status["missing_vars"] = missing_vars
            return JSONResponse(
                status_code=503,
                content=health_status
            )
        
        health_status["status"] = "healthy"
        return health_status
        
    except Exception as e:
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
    outbound_phone = os.getenv("OUTBOUND_PHONE_NUMBER")

    # Validate all required credentials
    missing_vars = []
    if not api_key:
        missing_vars.append("EIGHT_X_EIGHT_API_KEY")
    if not subaccount_id:
        missing_vars.append("EIGHT_X_EIGHT_SUBACCOUNT_ID")
    if not outbound_phone:
        missing_vars.append("OUTBOUND_PHONE_NUMBER")
    
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