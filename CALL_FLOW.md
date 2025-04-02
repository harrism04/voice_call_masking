# Call Masking Flow

This diagram illustrates the call masking flow implemented in this service.

```mermaid
%%{init: {
  'theme': 'base', 
  'themeVariables': {
    'primaryColor': '#BB2528',
    'primaryTextColor': '#fff',
    'primaryBorderColor': '#7C0000',
    'lineColor': '#F8B229',
    'secondaryColor': '#006100',
    'tertiaryColor': '#fff',
    'textColor': '#fff',
    'noteTextColor': '#333',
    'noteBkgColor': '#fff5ad',
    'edgeLabelBackground': 'rgba(0,0,0,0.5)',
    'background': 'transparent'
  }
}}%%
sequenceDiagram
    participant Caller as Client
    participant ProxyNumber as 8x8 Virtual Number
    participant Server as Integration Middleware
    participant VoiceAPI as 8x8 Voice API
    participant Recipient as Recipient

    rect rgb(100, 150, 220)
        note right of Caller: 1. Call Initiation
        Caller->>ProxyNumber: Calls virtual number
        ProxyNumber->>Server: Webhook: CALL_RECEIVED
        Note over Server: Validates webhook payload
        Server->>VoiceAPI: Request call masking
        Note over VoiceAPI: Plays waiting message
    end

    rect rgb(100, 180, 120)
        note right of VoiceAPI: 2. Call Connection
        VoiceAPI->>Recipient: Makes outbound call
        Note over VoiceAPI: Bridges both calls
        Recipient-->>Caller: Connected call
        Note over Caller,Recipient: Masked conversation
    end

    rect rgb(200, 120, 120)
        note right of Server: 3. Call Monitoring
        Note right of Server: Real numbers hidden<br/>from both parties
        VoiceAPI-->>Server: Call status updates
        Server->>Server: Tracks call in active_calls
    end
```

## Flow Description

1. A caller dials the virtual number assigned to the service
2. The service receives a webhook notification for the incoming call
3. The server validates the call information and initiates call masking
4. Voice API plays a waiting message to the caller
5. The service makes an outbound call to the forwarded number
6. Both calls are bridged while maintaining number privacy
7. The conversation proceeds with both parties' real numbers masked
8. The service tracks active calls and their status

## Key Components

- **Virtual Number**: The public-facing number that callers dial
- **Server**: FastAPI service handling webhook events and call control
- **Voice API**: 8x8 Voice API handling call execution and bridging
- **Forwarded Number**: The final destination number (kept private)