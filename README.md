# Food Scanner App

A comprehensive full-stack application that helps users make informed health decisions by scanning physical food products. 

The system uses a state-of-the-art dual-pipeline approach (Barcode + Label OCR) and provides real-time personalized health insights, additive warnings, and healthy alternatives powered by an intelligent RAG (Retrieval-Augmented Generation) backend.

## 🌟 Introduction

NutriScanner (Food Scanner) allows users to scan the barcode or directly photograph the nutrition label/ingredients of any packaged food item. The core objective is not simply to display static nutritional facts, but to actively evaluate the health impact of the product. The system cross-references ingredients against an "Additives Expert" knowledge base, calculates a personalized health score according to user dietary preferences (e.g., Vegan, Gluten-Free, No Sugar), and optionally uses an LLM-driven RAG pipeline to interpret complex chemical additives or compliance warnings (e.g., FSSAI standards).

Users must be able to log in, save their scan history, configure health preferences, and track their wellness trends over time.

---

## 🛠 Tech Stack

The application employs a decoupled architecture separating the user-facing Progressive Web App (PWA) from the heavy Python inference and data backends.

### Frontend
- **Framework:** Next.js (React 18)
- **Styling:** Tailwind CSS (with custom utility classes and animations)
- **Language:** JavaScript
- **Hosting / Deployment:** Vercel

### Backend
- **Framework:** Flask (Python 3.11)
- **Machine Learning & OCR:** 
  - XGBoost (for tabular health scoring modeling)
  - EasyOCR & OpenCV (for label text extraction)
  - SHAP (for Explainable AI feature impacts)
- **Data Processing:** NumPy, Ultralytics YOLO (if visual barcode detection is needed), PyZbar (for barcode decoding).
- **Server:** Gunicorn
- **Deployment:** Hugging Face Spaces (Docker containerized)

### Database Layer
- **SQLite (SQL):** Used for storing user profiles, scan histories, and user dietary preferences (`food_scanner.db`).
- **Local JSON / TinyDB caches:** Used for persisting GTIN (barcode) lookup caches locally (`nutrition_cache.db` / `gtin_cache.db`).

---

## 🏗 System Architecture & Methodology

The backend employs a unique **Dual Scan Pipeline** to maximize successful product identification.

### 1. The Consumer Scan Request
The user interacts with the Next.js frontend, configuring their dietary preferences in their profile (e.g. `Vegan: True`). When they want to analyze a product, they open the camera via the web app. The frontend captures an image natively via the browser (`getUserMedia`) and allows the user to select either **"Scan Barcode (Fast)"** or **"Scan Label (Deep Analysis)"**.

The captured image is converted to a base64 string and POSTed to the Flask API.

### 2. The Analysis Pipelines

#### Pipeline A: Barcode Flow (`POST /api/scan`)
This is the primary, fastest route.
1. **Extraction:** The backend decodes the image and uses `pyzbar` to extract the GTIN (Global Trade Item Number).
2. **Database Lookup:** The GTIN is queried against our local cache, and if not present, enriched via external aggregators (like OpenFoodFacts).
3. **Data Retrieval:** Nutritional data (per 100g) and the RAW ingredient list string are passed down into the Scoring Engine.

#### Pipeline B: Label / OCR Flow (`POST /api/scan-label`)
This route is used when a barcode isn't available, or for complex Indian/regional products.
1. **Computer Vision:** `EasyOCR` processes the image to extract raw text blocks.
2. **NLP Extraction:** NER (Named Entity Recognition) regex parsers or lightweight ML models extract key fields (Sugar, Sodium, Proteins, etc.) and isolate the "Ingredients" text block from the noisy OCR output.
3. **Product Correlation:** If a product name is provided by the user, the OCR text is cross-referenced with potential database matches.

### 3. The Assessment Engine 
Regardless of which pipeline generated the raw nutritional data, the data flows into a unified evaluation engine:

1. **Additives Expert:** 
   The raw ingredient string is passed to an NLP-based `AdditivesExpert`. It tokenizes the string and searches for hundreds of known chemical additives, preservatives (e.g., INS numbers, "Tartrazine"), and allergens. It calculates an "Additive Risk Impact" (Safe, Moderate Risk, High Risk).
   
2. **Health Score Ensemble (XGBoost):**
   A trained XGBoost model takes the continuous features (Sugar (g), Fat (g), Calories) combined with the newly calculated `Additive Risk Impact` to project a raw baseline health score out of 10.

3. **Preference Application & Override Engine:**
   The User ID token is checked against the local SQLite Database. If the user is marked as "Vegan", the engine scans the ingredient list for animal derivatives (milk, casein, whey, gelatin). If found, the system triggers a **hard override**, automatically forcing the product's health status to `RED (HARMFUL)` and appending an explanation warning. Similar overrides exist for Celiacs (Gluten free) or Diabetics (No Sugar).

4. **Optional RAG Enrichment:**
   If enabled via environment variables, the ingredient text is sent to an external LLM RAG pipeline to generate plain-english warnings ("Contains Artificial Colors linked to hyperactivity") and suggest healthy alternatives based on user history.

### 4. Response & Frontend Visualization
The backend synthesizes this data into a structured JSON payload:
- Health Color (`GREEN` / `YELLOW` / `RED`)
- Raw Score (x.x / 10)
- Array of Flagged Additives + Risk Levels
- Array of User Preference Warnings

The Next.js app renders this data dynamically. It features a custom animated `ScoreReveal` overlay component that steps the user through the discoveries (Nutrition -> Additives -> Final Score). Finally, the backend logs the exact score, image metadata, and timestamp to the SQLite DB, instantly allowing the user to view this item populated in their "Recent Scans" dashboard tab.
