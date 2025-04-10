<h1 align="center">📞 8x8 Voice API (CPaaS) - Call Masking Demo</h1>

<p align="center">
This project demonstrates call masking functionality using the 8x8 Voice API. When a customer calls your virtual number, the call is masked and forwarded to your actual phone number, protecting your privacy while maintaining communication.
</p>

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Setup Guide](#-setup-guide)
- [Try it out!](#-try-it-out)
- [Additional Information](#ℹ️-additional-information)

## ✨ Features

- Incoming call masking for privacy protection
- Real-time webhook handling for call events
- Detailed logging for debugging and monitoring
- Docker containerization for easy deployment
- Ngrok integration for local webhook testing

## 📋 Prerequisites

<details>
  <summary>🔑 Required Resources</summary>

  ### Development Environment
  - Docker and Docker Compose
  - [Ngrok Account](https://ngrok.com/signup) with:
    - [Authtoken](https://dashboard.ngrok.com/authtokens)
    - [Static Domain](https://dashboard.ngrok.com/domains) (free tier includes 1 static URL)

  ### 8x8 Connect Resources
  - Connect Portal Account with:
    - API Key
    - Subaccount ID
    - Virtual Number assigned to your Subaccount

  ### Test Phone Numbers
  - Source Number: Your phone to initiate test calls
  - Destination Number (`FORWARDED_PHONE_NUMBER`): Phone to receive forwarded calls

  > **Note:** In production environments:
  > - Source represents customer/patient/passenger phones
  > - Destination represents service provider/doctor/driver phones
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

## 📚 Try it out!

<details>
  <summary>Experiencing Call Masking flow</summary>

1. **Initiate Test Call**
   - Using your Source Number (test phone). In production this will be the client/service provider whose privacy need to be protected.
   - Call the Virtual Number (assigned in 8x8 Connect Portal)

2. **Observe Call Masking**
   - Call is forwarded to your Destination Number (`FORWARDED_PHONE_NUMBER`) - this could be a spare phone, a colleague, etc. In production this will be the service provider/client whose privacy need to be protected.
   - Source Number sees the Virtual Number as caller ID
   - Destination Number sees the Virtual Number as caller ID
   - Complete number privacy maintained for both parties
  
  > **Note:** In production environments:
  > - Source represents customer/patient/passenger phones
  > - Destination represents service provider/doctor/driver phones

## ℹ️ Additional Information

<details>
  <summary>📝 Logging</summary>
  
  You can view logs of inbound/outbound API requests by going to:
  
  1. https://dashboard.ngrok.com/ → "Traffic Inspector" in the left menu (Recommended)
  2. http://localhost:4040/ (legacy but cleaner interface, sometimes does not work).
  3. Docker Desktop logs by clicking on the container name
     ![image](https://github.com/user-attachments/assets/2ec97113-4f0d-405c-8b42-4954920e3484)

     
</details>

<details>
  <summary>🔍 Troubleshooting</summary>

1. Common Issues:
   - Webhook connectivity issues: Check Ngrok status and 8x8 Connect console
   - Call forwarding issues: Verify your FORWARDED_PHONE_NUMBER is correct and in international format
   - Authentication failures: Verify API keys and credentials

2. Getting Help:
   - Check 8x8 Voice API documentation
   - Monitor application logs in the docker container as per screenshot above, or using the command `docker-compose logs -f` in the container 
</details>
