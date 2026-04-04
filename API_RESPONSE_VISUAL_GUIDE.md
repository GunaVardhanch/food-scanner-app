# API Response Format Structure - Visual Reference

## REQUEST → RESPONSE FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                           │
│                    (React Frontend)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ POST Request
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Request Format:                                                 │
│ {                                                               │
│   "message": "What are the calories in an idli?"               │
│ }                                                               │
│                                                                 │
│ Headers:                                                        │
│ - Authorization: Bearer {JWT_TOKEN}                            │
│ - Content-Type: application/json                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ /api/chat
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              FLASK BACKEND (Python)                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. Validate JWT Token                                     │  │
│  │ 2. Extract user_id from token                             │  │
│  │ 3. Prepare conversation history                           │  │
│  │ 4. Construct messages array with system prompt            │  │
│  │ 5. Call chatbot_service.chat(user_message)               │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Groq API Client
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│         GROQ API (Cloud)                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Model: llama-3.1-70b-versatile                            │  │
│  │                                                           │  │
│  │ Messages:                                                 │  │
│  │ [                                                         │  │
│  │   {"role": "system", "content": "You are a..."},          │  │
│  │   {"role": "user", "content": "What are calories..."}    │  │
│  │ ]                                                         │  │
│  │                                                           │  │
│  │ Parameters:                                               │  │
│  │ - temperature: 0.7                                        │  │
│  │ - max_tokens: 500                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Structured Response
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ GROQ Response Object:                                           │
│ {                                                               │
│   "choices": [{                                                 │
│     "message": {                                                │
│       "role": "assistant",                                      │
│       "content": "An idli typically contains 60-75..."          │
│     },                                                          │
│     "finish_reason": "stop"                                     │
│   }],                                                           │
│   "usage": {                                                    │
│     "prompt_tokens": 85,                                        │
│     "completion_tokens": 42,                                    │
│     "total_tokens": 127                                         │
│   },                                                            │
│   "model": "llama-3.1-70b-versatile",                          │
│   "id": "req_1234567890",                                       │
│   "created": 1712234662                                         │
│ }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Parse & Wrap
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND RESPONSE WRAPPER                           │
│                                                                 │
│ 200 OK HTTP Response:                                           │
│ {                                                               │
│   "status": "success",                                          │
│   "timestamp": "2026-04-04T08:24:22.756718",                   │
│   "request": {                                                  │
│     "model": "llama-3.1-70b-versatile",                        │
│     "user_message": "What are the calories in an idli?",       │
│     "temperature": 0.7,                                         │
│     "max_tokens": 500                                           │
│   },                                                            │
│   "response": {                                                 │
│     "message": {                                                │
│       "role": "assistant",                                      │
│       "content": "An idli typically contains 60-75..."         │
│     },                                                          │
│     "finish_reason": "stop"                                     │
│   },                                                            │
│   "usage": {                                                    │
│     "prompt_tokens": 85,                                        │
│     "completion_tokens": 42,                                    │
│     "total_tokens": 127                                         │
│   },                                                            │
│   "api_metadata": {                                             │
│     "model": "llama-3.1-70b-versatile",                        │
│     "request_id": "req_1234567890",                             │
│     "created": 1712234662                                       │
│   }                                                             │
│ }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ JSON Parsing
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              FRONTEND RENDERING                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Message Display:                                           │  │
│  │ ┌─────────────────────────────────────────────────────┐   │  │
│  │ │ 🤖 Assistant (08:24:22)                            │   │  │
│  │ │ An idli typically contains 60-75 calories per      │   │  │
│  │ │ piece. They are made from fermented rice and      │   │  │
│  │ │ lentil batter...                                   │   │  │
│  │ └─────────────────────────────────────────────────────┘   │  │
│  │                                                            │  │
│  │ Token Usage: 127 total (85 prompt + 42 completion)       │  │
│  │ Response Time: ~2.1 seconds                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## RESPONSE STATUS CODES & FORMATS

### ✅ SUCCESS (200)
```json
{
  "status": "success",
  "response": "AI-generated answer...",
  "usage": { "total_tokens": 127 }
}
```

### ⚠️ CLIENT ERROR (400)
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Message field is required"
  }
}
```

### 🔐 AUTHENTICATION ERROR (401)
```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing authentication token"
  }
}
```

### 🔴 SERVER ERROR (500)
```json
{
  "status": "error",
  "error": {
    "code": "GROQ_API_ERROR",
    "message": "External API error occurred"
  }
}
```

---

## CONVERSATION HISTORY STRUCTURE

```
User Conversation:
┌─────────────────────────────────────────┐
│ Message 1 (User)                        │
│ "What are the calories in an idli?"    │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ Message 2 (Assistant)                   │
│ "An idli typically contains 60-75..."   │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ Message 3 (User)                        │
│ "Is biryani healthy for weight loss?"  │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ Message 4 (Assistant)                   │
│ "Biryani is calorie-dense..."           │
└─────────────────────────────────────────┘
          ↓
   (Limit: 20 Messages per session)
   (Last 10 exchanges kept in memory)
```

---

## TOKEN USAGE CALCULATION

```
┌──────────────────────────────────────────┐
│ Single Request:                          │
│                                          │
│ Prompt Tokens:       85  (input)        │
│ Completion Tokens:   42  (output)       │
│ ────────────────────────────────────────│
│ Total Tokens:       127                 │
│                                          │
│ Cost (Groq Free):  $0.00 (free tier)   │
│ Cost (Paid):       ~$0.001              │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ Per Month (1000 conversations avg):      │
│                                          │
│ Avg tokens/conversation:  150           │
│ Total tokens:             150,000       │
│ Estimated cost:           ~$0.30        │
│                                          │
│ Groq pricing:             $0.002/1M     │
│ (Much cheaper than OpenAI)               │
└──────────────────────────────────────────┘
```

---

## ERROR RESPONSE TYPES

| Error Type | Code | HTTP | When |
|-----------|------|------|------|
| Missing Message | `INVALID_REQUEST` | 400 | No message field |
| Invalid Token | `UNAUTHORIZED` | 401 | Token expired/invalid |
| Rate Limited | `RATE_LIMIT` | 429 | Too many requests |
| Model Error | `MODEL_ERROR` | 500 | Groq API issue |
| Server Error | `SERVER_ERROR` | 500 | Backend crash |

---

## API ENDPOINTS REFERENCE

### Send Message
```
POST /api/chat
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "message": "Query about food..."
}

Response (200):
{
  "response": "AI answer...",
  "user_id": "user_123",
  "timestamp": "2026-04-04T08:24:22..."
}
```

### Clear History
```
POST /api/chat/clear
Authorization: Bearer {token}

Response (200):
{
  "message": "Chat history cleared",
  "cleared_messages": 4,
  "cleared_tokens": 212
}
```

---

## FRONTEND STATE STRUCTURE

```javascript
{
  // Message array
  messages: [
    {
      id: "msg_001",
      text: "What is biryani?",
      sender: "user",      // "user" | "bot" | "error"
      timestamp: 1712234620000
    },
    {
      id: "msg_002",
      text: "Biryani is a rice dish...",
      sender: "bot",
      timestamp: 1712234625000
    }
  ],
  
  // UI state
  isLoading: false,           // Show loading dots
  hasError: false,            // Show error banner
  errorMessage: null,         // Error text
  conversationActive: true,   // Session status
  
  // Metadata
  tokenCount: 127,
  conversationId: "conv_789"
}
```

---

## COMPLETE EXAMPLE: END-TO-END

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FULL FLOW EXAMPLE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: USER TYPES & SENDS
  User Input: "How many calories in sambar?"
  ↓
STEP 2: FRONTEND SENDS REQUEST
  POST /api/chat
  {
    "message": "How many calories in sambar?",
    "Authorization": "Bearer eyJhbGc..."
  }
  ↓
STEP 3: BACKEND PROCESSES
  ✓ Validates token → extracts user_id
  ✓ Loads conversation history (last 20 messages)
  ✓ Constructs messages array:
    [
      {role: "system", content: "You are a food assistant..."},
      {role: "user", content: "How many calories in sambar?"}
    ]
  ✓ Calls: chatbot_service.chat(message, model="llama-3.1-70b-versatile")
  ↓
STEP 4: GROQ API PROCESSES
  ✓ Receives 2 messages (system + user)
  ✓ Generates response using llama-3.1-70b-versatile model
  ✓ Returns structured response with tokens
  ↓
STEP 5: BACKEND WRAPS & RETURNS
  200 OK
  {
    "status": "success",
    "response": "Sambar typically contains 80-120 calories per cup...",
    "usage": {"total_tokens": 143},
    "timestamp": "2026-04-04T08:24:22..."
  }
  ↓
STEP 6: FRONTEND DISPLAYS
  🤖 Assistant (08:24:22)
  Sambar typically contains 80-120 calories per cup...
  
  Input remaining: disabled (API processing)
  ↓ (after 2-3 seconds)
  Input enabled for next message
```

---

## FORMAT SCHEMA CHECKLIST

✅ **Request Schema**
- [ ] Has "message" field (string, non-empty)
- [ ] Has Authorization header with Bearer token
- [ ] Content-Type is application/json

✅ **Response Schema**
- [ ] Has "status" field ("success" or "error")
- [ ] Has "response" field (string, AI content)
- [ ] Has "timestamp" field (ISO 8601)
- [ ] Has "usage" field (tokens breakdown)
- [ ] Has "metadata" field (for debugging)

✅ **Error Schema**
- [ ] Has "status": "error"
- [ ] Has "error.code" (error identifier)
- [ ] Has "error.message" (human-readable)
- [ ] Has "timestamp" field

---

## INTEGRATION CHECKLIST

Before going to production:

- [ ] Set `GROQ_API_KEY` in `.env`
- [ ] Verify model has access: `llama-3.1-70b-versatile`
- [ ] Test `/api/chat` endpoint manually
- [ ] Verify conversation history works
- [ ] Check `/api/chat/clear` endpoint
- [ ] Test with real frontend
- [ ] Monitor token usage
- [ ] Set up error logging
- [ ] Implement rate limiting
- [ ] Add conversation audit logs

---

**Format Structure Documentation** - April 4, 2026  
**Status**: ✅ Complete | ⏳ Ready for Production
