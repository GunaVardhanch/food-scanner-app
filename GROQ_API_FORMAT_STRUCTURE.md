# Groq Chatbot API - Response Format Structure

## API Response Format Documentation

Based on the Groq Python SDK integration, here's the complete response format structure:

---

## 1. SUCCESSFUL CHAT RESPONSE

### Request Format
```json
{
  "model": "llama-3.1-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "You are a multilingual food and nutrition assistant..."
    },
    {
      "role": "user",
      "content": "What are the calories in an idli?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

### Response Format (SUCCESS)
```json
{
  "status": "success",
  "timestamp": "2026-04-04T08:24:22.756718",
  
  "request": {
    "model": "llama-3.1-70b-versatile",
    "user_message": "What are the calories in an idli?",
    "temperature": 0.7,
    "max_tokens": 500
  },
  
  "response": {
    "message": {
      "role": "assistant",
      "content": "An idli typically contains 60-75 calories per piece. They are made from fermented rice and lentil batter, making them light and digestible. For context: 2-3 idlis with a standard serving of sambar (vegetable stew) provides around 150-200 calories."
    },
    "finish_reason": "stop"
  },
  
  "usage": {
    "prompt_tokens": 85,
    "completion_tokens": 42,
    "total_tokens": 127
  },
  
  "api_metadata": {
    "model": "llama-3.1-70b-versatile",
    "request_id": "req_1234567890abcdef",
    "created": 1712234662
  }
}
```

---

## 2. ERROR RESPONSE FORMATS

### 2a. Model Decommissioned Error
```json
{
  "status": "error",
  "error": {
    "type": "invalid_request_error",
    "code": "model_decommissioned",
    "message": "The model `mixtral-8x7b-32768` has been decommissioned and is no longer supported. Please refer to https://console.groq.com/docs/deprecations for a recommendation on which model to use instead."
  },
  "timestamp": "2026-04-04T08:24:22.756718"
}
```

### 2b. Model Not Found Error
```json
{
  "status": "error",
  "error": {
    "type": "invalid_request_error",
    "code": "not_found",
    "message": "The model `invalid-model-name` does not exist or you don't have access to it."
  },
  "timestamp": "2026-04-04T08:24:22.756718"
}
```

### 2c. Authentication Error
```json
{
  "status": "error",
  "error": {
    "type": "authentication_error",
    "code": "invalid_api_key",
    "message": "Invalid API key provided. Please check your credentials."
  },
  "timestamp": "2026-04-04T08:24:22.756718"
}
```

### 2d. Rate Limit Error
```json
{
  "status": "error",
  "error": {
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please wait before making another request."
  },
  "timestamp": "2026-04-04T08:24:22.756718"
}
```

---

## 3. CONVERSATION HISTORY STRUCTURE

### Multi-turn Conversation Format
```json
{
  "conversation": {
    "user_id": "user_123",
    "session_id": "session_456",
    "created_at": "2026-04-04T08:00:00.000000",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "What are the calories in an idli?",
        "timestamp": "2026-04-04T08:24:00.000000"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "An idli typically contains 60-75 calories per piece...",
        "timestamp": "2026-04-04T08:24:05.000000",
        "tokens_used": 127
      },
      {
        "id": "msg_003",
        "role": "user",
        "content": "Is biryani healthy for weight loss?",
        "timestamp": "2026-04-04T08:24:10.000000"
      },
      {
        "id": "msg_004",
        "role": "assistant",
        "content": "Biryani is calorie-dense (around 300-400 cal per serving) due to ghee and oil. For weight loss, it's better to consume in moderation or choose lighter rice dishes...",
        "timestamp": "2026-04-04T08:24:15.000000",
        "tokens_used": 85
      }
    ],
    "total_messages": 4,
    "total_tokens_used": 212,
    "status": "active"
  }
}
```

---

## 4. BATCH REQUEST/RESPONSE

### Batch Conversation Clear
```json
{
  "action": "clear_history",
  "endpoint": "POST /api/chat/clear",
  "request": {
    "Authorization": "Bearer {token}",
    "Content-Type": "application/json"
  },
  "response": {
    "status": "success",
    "message": "Chat history cleared successfully",
    "timestamp": "2026-04-04T08:24:22.756718",
    "user_id": "user_123",
    "cleared_messages": 4,
    "cleared_tokens": 212
  }
}
```

---

## 5. AVAILABLE MODELS & SPECIFICATIONS

### Current Available Groq Models
```json
{
  "models": [
    {
      "id": "mixtral-8x7b-32768",
      "name": "Mixtral 8x7B",
      "context_tokens": 32768,
      "status": "DEPRECATED (use llama-3.1-70b-versatile)",
      "recommended_use": "General purpose"
    },
    {
      "id": "llama-3.1-70b-versatile",
      "name": "Meta Llama 3.1 70B Versatile",
      "context_tokens": 128000,
      "status": "ACTIVE",
      "recommended_use": "Food queries, multilingual, general assistant"
    },
    {
      "id": "llama-3.1-8b-instant",
      "name": "Meta Llama 3.1 8B Instant",
      "context_tokens": 128000,
      "status": "ACTIVE",
      "recommended_use": "Fast responses, lower latency"
    },
    {
      "id": "gemma-7b-it",
      "name": "Google Gemma 7B It",
      "context_tokens": 6144,
      "status": "ACTIVE",
      "recommended_use": "Instruction-following tasks"
    }
  ]
}
```

---

## 6. BACKEND INTEGRATION RESPONSE WRAPPER

### Flask API Response Format `/api/chat`
```json
{
  "status": 200,
  "success": true,
  "data": {
    "response": "An idli typically contains 60-75 calories per piece...",
    "user_id": "user_123",
    "conversation_id": "conv_789",
    "timestamp": "2026-04-04T08:24:22.756718"
  },
  "metadata": {
    "api_version": "1.0",
    "endpoint": "/api/chat",
    "method": "POST"
  }
}
```

### Flask API Error Response
```json
{
  "status": 400,
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Message field is required",
    "details": "Please provide a non-empty 'message' in the request body"
  },
  "timestamp": "2026-04-04T08:24:22.756718"
}
```

---

## 7. FRONTEND COMPONENT STATE STRUCTURE

### React FoodChatbot Component State
```javascript
{
  messages: [
    {
      id: "msg_001",
      text: "What is the calorie content of biryani?",
      sender: "user",
      timestamp: 1712234620000
    },
    {
      id: "msg_002",
      text: "Biryani typically contains 300-400 calories per serving...",
      sender: "bot",
      timestamp: 1712234625000
    },
    {
      id: "msg_003",
      text: "error_message_text",
      sender: "error",
      timestamp: 1712234630000
    }
  ],
  isLoading: false,
  hasError: false,
  errorMessage: null,
  conversationActive: true
}
```

---

## 8. USAGE STATISTICS

### Token Usage Structure
```json
{
  "conversation_stats": {
    "total_messages": 4,
    "total_exchanges": 2,
    "tokens": {
      "total_prompt_tokens": 342,
      "total_completion_tokens": 156,
      "total_tokens": 498,
      "estimated_cost_usd": "$0.00125"
    },
    "models_used": ["llama-3.1-70b-versatile"],
    "duration_seconds": 8.5,
    "average_response_time_ms": 2125
  }
}
```

---

## 9. ENVIRONMENT CONFIGURATION

### Backend Environment Variables
```bash
# .env file
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_MAX_TOKENS=500
GROQ_TEMPERATURE=0.7
CONVERSATION_HISTORY_LIMIT=10
```

---

## 10. COMPLETE FLOW EXAMPLE

### Full Request-Response Cycle
```
CLIENT REQUEST
↓
POST /api/chat
Headers: { Authorization: "Bearer {token}", Content-Type: "application/json" }
Body: { "message": "How many calories in sambar?" }
↓
BACKEND PROCESSING
- Validate authentication token
- Prepare system + user message
- Call Groq API with llama-3.1-70b-versatile
↓
GROQ API RESPONSE
{
  "choices": [{
    "message": { "role": "assistant", "content": "Sambar typically contains..." },
    "finish_reason": "stop"
  }],
  "usage": { "prompt_tokens": 95, "completion_tokens": 48, "total_tokens": 143 }
}
↓
BACKEND RESPONSE
200 OK
{
  "response": "Sambar typically contains 80-120 calories per cup...",
  "user_id": "user_123",
  "timestamp": "2026-04-04T08:24:22.756718"
}
↓
FRONTEND RENDERING
Display message in chat bubble
Update message history
Show token usage info
```

---

## Key Points

✅ **Response Structure**: Consistent JSON format with status, data, and metadata  
✅ **Error Handling**: All errors include type, code, and descriptive message  
✅ **Token Tracking**: Every response includes token usage for cost calculation  
✅ **Timestamps**: ISO 8601 format for all temporal data  
✅ **Authentication**: Bearer token required for all endpoints  
✅ **Scalability**: Conversation history limited to 10 exchanges (20 messages)  
✅ **Models**: Currently using llama-3.1-70b-versatile (updated from deprecated mixtral)

---

**Last Updated**: April 4, 2026  
**API Status**: Operational with current models  
**Documentation Version**: 1.0.0
