# Shabari - Food & Nutrition Chatbot

## Overview

Shabari is an AI-powered food and nutrition assistant integrated into the Aahar meal planner app. It uses the **Groq API** for fast, multilingual responses to user queries about:

- Food items and nutrition facts
- Recipes and cooking instructions
- Calorie information
- Meal suggestions
- Dietary advice (basic, non-medical)

The chatbot automatically detects user language and responds in the same language.

---

## Setup Instructions

### 1. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for a free account
3. Navigate to **API Keys** section
4. Create a new API key
5. Copy the key

### 2. Backend Configuration

#### Option A: Environment Variable (Recommended)

Create a `.env` file in the `backend/` directory:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

#### Option B: System Environment Variable

Set the environment variable system-wide:

```bash
# Linux/Mac
export GROQ_API_KEY="your_groq_api_key_here"

# Windows PowerShell
$env:GROQ_API_KEY = "your_groq_api_key_here"
```

### 3. Install Dependencies

```bash
# Backend
pip install groq

# Frontend (already included in package.json)
npm install
```

### 4. Start the Application

```bash
# Backend
cd backend
python run_local.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

---

## API Endpoints

### Send Chat Message

**Endpoint:** `POST /api/chat`

**Authentication:** Required (Bearer token)

**Request:**
```json
{
  "message": "What are the calories in an idli?"
}
```

**Response:**
```json
{
  "response": "An idli typically contains 60-80 calories per piece...",
  "user_id": 123
}
```

### Clear Chat History

**Endpoint:** `POST /api/chat/clear`

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "message": "Chat history cleared"
}
```

---

## Features

### 1. Multilingual Support

The chatbot automatically detects input language and responds in:
- English
- Hindi
- Telugu
- Tamil
- And 100+ other languages

### 2. Conversation Context

- Maintains conversation history for context-aware responses
- Keeps last 10 exchanges (20 messages) for performance
- Users can clear history anytime

### 3. Response Types

The chatbot handles various query types:

| Query Type | Example | Response |
|-----------|---------|----------|
| Calories | "idli calories" | Calorie info + portion size |
| Recipe | "biryani recipe" | Step-by-step instructions |
| Ingredients | "What's in dal?" | Ingredient list |
| Health Tips | "weight loss food" | 2-3 practical suggestions |
| Nutrition | "protein in chicken" | Nutritional breakdown |

### 4. Smart Features

✅ Detects language automatically  
✅ Provides approximate values when exact data unknown  
✅ Indian food focus by default  
✅ Avoids medical/extreme diet advice  
✅ Keeps responses concise and friendly  
✅ No unnecessary greetings or emojis  

---

## System Prompt

The chatbot uses a carefully crafted system prompt for optimal responses:

- **Accuracy**: Realistic, practical answers
- **Clarity**: Concise, easy to understand
- **Context**: Indian food preference unless specified
- **Safety**: No medical or unsafe advice
- **Style**: Friendly but direct, no filler text

---

## Frontend Integration

### Using the Chatbot

The chatbot UI appears as a bottom sheet modal in the app:

1. Click the 💬 icon in the bottom navigation
2. Type your food/nutrition query
3. Get instant AI-powered response
4. Clear history with 🗑️ button

### Component Usage

```jsx
<FoodChatbot 
  isOpen={showChatbot} 
  onClose={() => setShowChatbot(false)}
  token={authToken}
/>
```

---

## Troubleshooting

### "Groq client not initialized"
- Check GROQ_API_KEY environment variable is set
- Verify `pip install groq` was successful
- Restart backend server

### "401 Unauthorized"
- Ensure valid authentication token is passed
- Check token is not expired
- Verify user is logged in

### "No response from chatbot"
- Check Groq API quota (free tier has limits)
- Verify internet connectivity
- Check backend logs for errors

### "Response takes too long"
- Groq API might be overloaded
- Try a simpler query first
- Check network latency

---

## Performance & Limits

### Free Tier (Groq)
- Rate limit: ~100 requests per minute
- Model: mixtral-8x7b-32768
- Response time: ~200-500ms average

### Optimization Tips
- Keep conversation history short (automatically managed)
- Use specific queries for faster responses
- Avoid very long messages

---

## Models Available

The chatbot uses **Mixtral 8x7B** by default, but you can change models in the backend:

```python
# In backend/app/services/chatbot_service.py
response = chatbot.chat(user_message, model="mixtral-8x7b-32768")
```

Other available Groq models:
- `mixtral-8x7b-32768` (default, best for food queries)
- `llama2-70b-4096` (larger context)
- `gemma-7b-it` (faster responses)

---

## Privacy & Data

- Chat messages are tied to authenticated users
- Conversation history stored temporarily in memory
- No conversation data persisted to disk
- Users can clear history anytime

---

## Future Enhancements

Potential improvements:
- 🔄 Persist conversation history to database
- 🖼️ Image analysis for food recognition (integrate with barcode scanner)
- 📊 Personalized recommendations based on user profile
- 🌍 Localized food databases per region
- 🎯 Voice input/output support
- 💾 Export meal suggestions as PDF

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Groq API documentation: https://console.groq.com/docs
3. Check application logs: `backend/app.log`

---

**Last Updated:** April 4, 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅
