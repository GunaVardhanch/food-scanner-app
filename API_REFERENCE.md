# Aahar AI - API Reference

## Base URL
```
http://localhost:5001
```

## Authentication
All endpoints requiring authentication use Bearer token in the Authorization header:
```
Authorization: Bearer <token>
```

---

# Authentication Endpoints

## POST /auth/register
**Create a new user account**

### Request
```json
{
  "email": "user@example.com",
  "password": "SecurePassword@123"
}
```

### Response (201 Created)
```json
{
  "status": "ok",
  "message": "User created successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2026-04-04T10:30:00Z"
  }
}
```

### Error Responses
- **400 Bad Request**: Missing email or password
- **409 Conflict**: Email already exists
- **422 Unprocessable Entity**: Invalid email format

---

## POST /auth/login
**Authenticate user and receive Bearer token**

### Request
```json
{
  "email": "user@example.com",
  "password": "SecurePassword@123"
}
```

### Response (200 OK)
```json
{
  "status": "ok",
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

### Error Responses
- **400 Bad Request**: Missing email or password
- **401 Unauthorized**: Invalid credentials
- **404 Not Found**: User not found

---

## GET /auth/me
**Get current authenticated user info**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Response (200 OK)
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-04-04T10:30:00Z"
}
```

### Error Responses
- **401 Unauthorized**: Token missing or invalid
- **403 Forbidden**: Token expired

---

# Profile Management Endpoints

## GET /api/profile
**Retrieve user profile**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Response (200 OK) - Complete Profile
```json
{
  "user_id": 1,
  "age": 28,
  "gender": "Female",
  "weight": 65.5,
  "height": 165,
  "diet_type": "vegetarian",
  "state": "Maharashtra",
  "cuisine": "North Indian",
  "health_goal": "lose_weight",
  "weekly_budget": 3000,
  "activity_level": "moderate",
  "created_at": "2026-04-04 10:30:00",
  "updated_at": "2026-04-04 10:30:00",
  "profile_complete": true
}
```

### Response (200 OK) - Incomplete Profile
```json
{
  "user_id": 1,
  "profile_complete": false,
  "message": "No profile data yet. Complete onboarding to create profile."
}
```

### Error Responses
- **401 Unauthorized**: Token missing or invalid
- **500 Internal Server Error**: Database error

---

## POST /api/profile
**Create or update user profile**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Request Body
```json
{
  "age": 28,
  "gender": "Female",
  "weight": 65.5,
  "height": 165,
  "diet_type": "vegetarian",
  "state": "Maharashtra",
  "cuisine": "North Indian",
  "health_goal": "lose_weight",
  "weekly_budget": 3000,
  "activity_level": "moderate"
}
```

### Field Validation

| Field | Type | Range | Required | Values |
|-------|------|-------|----------|--------|
| age | integer | 10-120 | Yes | Any integer |
| gender | string | - | Yes | Male, Female, Other |
| weight | float | 20-300 | Yes | Kilograms |
| height | float | 100-250 | Yes | Centimeters |
| diet_type | string | - | Yes | veg, eggetarian, non-veg, vegan, jain, satvik |
| state | string | - | Yes | Any of 28 Indian states |
| cuisine | string | - | Yes | North Indian, South Indian, East Indian, West Indian, Continental |
| health_goal | string | - | Yes | lose_weight, gain_muscle, stay_healthy, pregnancy, diabetes, pcod, senior |
| weekly_budget | integer | 100-50000 | Yes | Indian Rupees |
| activity_level | string | - | Yes | sedentary, light, moderate, active |

### Response (200 OK)
```json
{
  "status": "ok",
  "user_id": 1,
  "profile": {
    "age": 28,
    "gender": "Female",
    "weight": 65.5,
    "height": 165,
    "diet_type": "vegetarian",
    "state": "Maharashtra",
    "cuisine": "North Indian",
    "health_goal": "lose_weight",
    "weekly_budget": 3000,
    "activity_level": "moderate",
    "created_at": "2026-04-04 10:30:00",
    "updated_at": "2026-04-04 10:30:00"
  },
  "profile_complete": true
}
```

### Error Responses

**400 Bad Request** - Validation Failed
```json
{
  "error": "Invalid data format: age must be between 10 and 120"
}
```

**401 Unauthorized** - Missing or Invalid Token
```json
{
  "error": "Unauthorized: Missing or invalid token"
}
```

**422 Unprocessable Entity** - Invalid Enum Value
```json
{
  "error": "Invalid diet_type. Must be one of: veg, eggetarian, non-veg, vegan, jain, satvik"
}
```

**500 Internal Server Error** - Database Error
```json
{
  "error": "Failed to save profile"
}
```

---

# Meal Plan Endpoints

## GET /api/meal-plan
**Retrieve user's meal plan**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Query Parameters
- `days` (optional): Number of days (default: 7)
- `format` (optional): "daily" or "weekly" (default: "weekly")

### Response (200 OK)
```json
{
  "user_id": 1,
  "meal_plan": [
    {
      "day": 1,
      "date": "2026-04-04",
      "meals": [
        {
          "type": "breakfast",
          "items": ["Bajra Roti", "Aloo Gobi", "Curd"],
          "calories": 450,
          "budget": 80
        },
        {
          "type": "lunch",
          "items": ["Rice", "Dal Tadka", "Green Salad"],
          "calories": 550,
          "budget": 120
        },
        {
          "type": "snack",
          "items": ["Makhane", "Chai"],
          "calories": 150,
          "budget": 30
        },
        {
          "type": "dinner",
          "items": ["Roti", "Mixed Vegetable Curry", "Raita"],
          "calories": 450,
          "budget": 100
        }
      ],
      "daily_total": {
        "calories": 1600,
        "budget": 330
      }
    }
  ],
  "weekly_summary": {
    "total_calories": 11200,
    "total_budget": 2310,
    "budget_limit": 3000
  }
}
```

### Error Responses
- **401 Unauthorized**: Token missing or invalid
- **404 Not Found**: Profile incomplete
- **500 Internal Server Error**: Generation failed

---

# Scan History Endpoints

## GET /api/scan/history
**Get user's food scan history**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Query Parameters
- `limit` (optional): Number of records (default: 20)
- `offset` (optional): Pagination offset (default: 0)

### Response (200 OK)
```json
{
  "scans": [
    {
      "id": 1,
      "barcode": "8901234567890",
      "product_name": "Britannia Good Day Biscuit",
      "category": "Snacks",
      "calories": 130,
      "protein": 2.5,
      "fat": 6.0,
      "carbs": 16.0,
      "scanned_at": "2026-04-04 15:30:00"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

---

## POST /api/scan
**Record a food scan**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Request
```json
{
  "barcode": "8901234567890",
  "product_name": "Britannia Good Day Biscuit",
  "quantity": 2
}
```

### Response (201 Created)
```json
{
  "status": "ok",
  "scan_id": 1,
  "product": {
    "name": "Britannia Good Day Biscuit",
    "calories": 130,
    "protein": 2.5,
    "fat": 6.0,
    "carbs": 16.0
  },
  "total_nutrition": {
    "calories": 260,
    "protein": 5.0,
    "fat": 12.0,
    "carbs": 32.0
  }
}
```

---

# Preferences Endpoints

## GET /api/preferences
**Get user dietary preferences**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Response (200 OK)
```json
{
  "user_id": 1,
  "no_sugar": true,
  "gluten_free": false,
  "low_sodium": false,
  "vegan": false
}
```

---

## POST /api/preferences
**Update dietary preferences**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Request
```json
{
  "no_sugar": true,
  "gluten_free": false,
  "low_sodium": true,
  "vegan": false
}
```

### Response (200 OK)
```json
{
  "status": "ok",
  "user_id": 1,
  "preferences": {
    "no_sugar": true,
    "gluten_free": false,
    "low_sodium": true,
    "vegan": false
  }
}
```

---

# Analytics Endpoints

## GET /api/analytics
**Get health and nutrition analytics**

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Query Parameters
- `period` (optional): "week", "month", "all" (default: "week")

### Response (200 OK)
```json
{
  "user_id": 1,
  "period": "week",
  "summary": {
    "total_scans": 15,
    "avg_daily_calories": 1800,
    "avg_daily_budget": 450,
    "budget_adherence": 95,
    "health_score": 78
  },
  "daily_stats": [
    {
      "date": "2026-04-04",
      "calories": 1650,
      "budget_spent": 420,
      "budget_limit": 428,
      "health_score": 82
    }
  ]
}
```

---

# Error Handling

## Common Error Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Token missing/invalid |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Invalid enum values |
| 429 | Too Many Requests | Rate limited |
| 500 | Server Error | Internal error |

---

# Rate Limiting

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1680614400
```

All endpoints are rate limited to 1000 requests per hour per user.

---

# Code Examples

## JavaScript/Fetch

### Get Profile with Bearer Token
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:5001/api/profile', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const profile = await response.json();
console.log(profile);
```

### Create/Update Profile
```javascript
const profile = {
  age: 28,
  gender: 'Female',
  weight: 65.5,
  height: 165,
  diet_type: 'vegetarian',
  state: 'Maharashtra',
  cuisine: 'North Indian',
  health_goal: 'lose_weight',
  weekly_budget: 3000,
  activity_level: 'moderate'
};

const response = await fetch('http://localhost:5001/api/profile', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(profile)
});

const result = await response.json();
console.log(result);
```

## Python/Requests

### Get Profile
```python
import requests

token = 'your-bearer-token-here'
headers = {'Authorization': f'Bearer {token}'}

response = requests.get(
    'http://localhost:5001/api/profile',
    headers=headers
)

profile = response.json()
print(profile)
```

### Create Profile
```python
import requests

token = 'your-bearer-token-here'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

data = {
    'age': 28,
    'gender': 'Female',
    'weight': 65.5,
    'height': 165,
    'diet_type': 'vegetarian',
    'state': 'Maharashtra',
    'cuisine': 'North Indian',
    'health_goal': 'lose_weight',
    'weekly_budget': 3000,
    'activity_level': 'moderate'
}

response = requests.post(
    'http://localhost:5001/api/profile',
    headers=headers,
    json=data
)

result = response.json()
print(result)
```

---

# CORS Configuration

The API is configured with CORS headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 3600
```

---

# Token Expiration

- **Token Lifespan**: 30 days
- **Issued At**: Upon successful login
- **Refresh**: Required login to get new token
- **Format**: JWT (HS256)

### Token Structure
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.   ← Header
eyJ1c2VyX2lkIjogMSwgImV4cCI6IDE2ODA2MTQ0MDB9. ← Payload
OLvEdvmIXqVFSr...              ← Signature
```

---

# Changelog

## v1.0.0 (2026-04-04)
- Initial API release
- Authentication endpoints
- Profile endpoints
- Preferences endpoints
- Scan history endpoints
- Analytics endpoints
