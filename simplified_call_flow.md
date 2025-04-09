# Voice Call Masking - Simplified Call Flow

```mermaid
sequenceDiagram
    participant Caller as Client
    participant VirtualNum as Virtual Number
    participant Masking as Call Masking API (main.py)
    participant Voice8x8 as 8x8 Voice API
    participant Provider as Service Provider
    
    rect rgb(100, 150, 220)
        note right of Caller: 1. Call Initiation
        Caller->>VirtualNum: Calls virtual number
        VirtualNum->>Masking: POST /api/webhooks/vca
        Note over Masking: Extracts caller & virtual number
        Masking->>Voice8x8: Callflow response with makeCall action
        Voice8x8->>Provider: Places outbound call
    end
    
    rect rgb(100, 180, 120)
        note right of Provider: 2. Call Connection
        Provider->>Voice8x8: Answers call
        Voice8x8-->>Caller: Bridges both calls
        Note over Caller,Provider: Conversation with masked numbers
    end
    
    rect rgb(200, 120, 120)
        note right of Caller: 3. Call Completion
        Caller->>Voice8x8: Ends call
        Voice8x8->>Masking: POST /api/webhooks/vss (COMPLETED)
        Note over Masking: Updates call status
    end
```

## Key Points

1. **Call Initiation**
   - Client calls the virtual number
   - System receives webhook notification
   - Call masking service initiates outbound call to provider

2. **Call Connection**
   - Provider answers the call
   - Voice API bridges both call legs
   - Both parties communicate with masked numbers

3. **Call Completion**
   - Call ends (by either party)
   - System receives session completion webhook
   - Call details are recorded for tracking
