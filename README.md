# 📞 8x8 Voice API (CPaaS) - Call Masking Demo

This project demonstrates call masking functionality using the 8x8 Voice API. When a customer calls your virtual number, the call is masked and forwarded to your actual phone number, protecting your privacy while maintaining communication.

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Setup Guide](#-setup-guide)
- [API Documentation](#-api-documentation)
- [Additional Information](#ℹ️-additional-information)

## ✨ Features

- Incoming call masking for privacy protection
- Real-time webhook handling for call events
- Detailed logging for debugging and monitoring
- Docker containerization for easy deployment
- Ngrok integration for local webhook testing

## 📋 Prerequisites

<details>
  <summary>🔑 Required accounts and resources</summary>
  
  - Docker and Docker Compose
  - 8x8 Connect Account with:
    - API Key
    - Subaccount ID
    - Virtual Number (for receiving masked calls)
  - Ngrok account with authtoken and a static domain for local testing
</details>

<details>
  <summary>🔄 Setting Up Ngrok</summary>
  
  This project requires ngrok with a static domain for webhook handling:

  - **Ngrok account**: Sign up at [ngrok.com](https://ngrok.com/signup)
  - **Static domain**: Head over to https://dashboard.ngrok.com/domains to create a static domain (Limited to 1 static url for free ngrok accounts)
  - **Authtoken**: Go to https://dashboard.ngrok.com/authtokens to create an authtoken
</details>

##  🚀 Setup Guide

<details>
  <summary>🐳 Quick Start with Docker (Recommended)</summary>
  
  1. Clone the repository:
     ```bash
     git clone https://github.com/harrism04/voice_callmasking_demo.git
     cd voice_callmasking_demo
     ```

  2. Set up environment variables:
     ```bash
     cp .env.example .env
     ```
     Edit `.env` and fill in your credentials:
     ```
     EIGHT_X_EIGHT_API_KEY=your_api_key_from_connect_portal
     EIGHT_X_EIGHT_SUBACCOUNT_ID=your_subaccount_id
     FORWARDED_PHONE_NUMBER=your_phone_number  # Number to forward masked calls to
     WEBHOOK_AUTH_TOKEN=your_randomly_generated_webhook_auth_token
     WEBHOOK_BASE_URL=your_static_ngrok_domain  # e.g., https://your-domain.ngrok-free.app
     NGROK_AUTHTOKEN=your_ngrok_authtoken
     ```

  3. Start the application:
     ```bash
     docker-compose up -d --build
     ```
     
     To check the status of your services:
     ```bash
     docker ps
     ```
     
     To view the ngrok tunnel URL:
     ```bash
     curl -s http://localhost:4040/api/tunnels
     ```

  4. Configure webhook in 8x8 Connect console:
     - Set up your webhook URL as: `{WEBHOOK_BASE_URL}/api/webhooks/mask`

The application is now ready to handle masked calls!
</details>

## 📚 API Documentation

<details>
  <summary>🔌 Webhook Endpoint</summary>

`POST /api/webhooks/mask`
   - Handles incoming call masking requests
   - When a call is received on your virtual number, it will be forwarded to your FORWARDED_PHONE_NUMBER
   - A brief message will be played to the caller indicating their call is being connected
   - No authentication required for incoming webhooks from 8x8

Example webhook payload from 8x8:
```json
{
    "payload": {
        "source": "+6591234567",
        "destination": "your_virtual_number"
    }
}
```
</details>

## ℹ️ Additional Information

<details>
  <summary>📝 Logging</summary>
  
  You can view logs of inbound/outbound API requests via ngrok's Traffic Inspector by going to:
  
  1. http://localhost:4040/ (legacy but cleaner interface)
  2. https://dashboard.ngrok.com/ → "Traffic Inspector" in the left menu
</details>

<details>
  <summary>🔍 Troubleshooting</summary>

1. Common Issues:
   - Webhook connectivity issues: Check Ngrok status and 8x8 Connect console
   - Call forwarding issues: Verify your FORWARDED_PHONE_NUMBER is correct and in international format
   - Authentication failures: Verify API keys and credentials

2. Getting Help:
   - Check 8x8 Voice API documentation
   - Monitor application logs using `docker-compose logs -f`
</details>
