# Food Scanner App

A full-stack application with a Next.js frontend and a FastAPI backend for scanning food products and analyzing nutritional content.

## Project Structure

- `frontend/`: Next.js application.
- `backend/`: FastAPI application (Dockerized).

## Deployment (Railway)

This project is configured to be deployed on [Railway](https://railway.app/).

### Steps to Deploy:

1.  **Push to GitHub**: Ensure your code is in a GitHub repository.
2.  **Create New Project**:
    - Go to Railway and click **"New Project"**.
    - Select **"Deploy from GitHub repo"**.
    - Choose this repository.
3.  **Automatic Detection**: Railway will detect the `railway.json` file and automatically create two services: `frontend` and `backend`.
4.  **Configure Environment Variables**:
    - In the `frontend` service settings, add an environment variable `NEXT_PUBLIC_API_URL` pointing to your backend URL (e.g., `https://backend-production.up.railway.app`).
5.  **Done!**: Your app will be live.

## Local Development

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
