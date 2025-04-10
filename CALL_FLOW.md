# Call Masking Flow

This diagram illustrates the actual implementation of call masking in this service.

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
    participant Source as Source Number
    participant VNumber as Virtual Number
    participant Server as FastAPI Server (main.py)
    participant Voice8x8 as 8x8 Voice API
    participant Dest as Destination Number

    rect rgb(100, 150, 220)
        note right of Source: 1. Call Initiation
        Source->>VNumber: Dials virtual number
        VNumber->>Server: POST /api/webhooks/vca
        Note over Server: Stores call context in active_calls
        Server->>Voice8x8: Returns makeCall action
    end

    rect rgb(100, 180, 120)
        note right of Voice8x8: 2. Call Bridging
        Voice8x8->>Dest: Outbound call from virtual number
        Note over Voice8x8: Bridges calls
        Note over Source,Dest: Masked conversation in progress
    end

    rect rgb(200, 120, 120)
        note right of Voice8x8: 3. Call Completion
        Voice8x8->>Server: POST /api/webhooks/vss
        Note over Server: Updates final call status
    end
```

## Implementation Details

1. **Call Initiation** (`/api/webhooks/vca`)
   - Client makes call to the virtual number
   - Receive incoming call webhook from 8x8
   - Validate required configuration (API key, subaccount, numbers)
   - Store call context in `active_calls` dictionary
   - Return callflow with `makeCall` action

2. **Call Management**
   - Virtual number used as source for outbound call
   - Both parties see only the virtual number

3. **Call Completion** (`/api/webhooks/vss`)
   - Either party hangs up
   - Receive final call status webhook
   - Update call record in `active_calls`
   - Track call completion status
