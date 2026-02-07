# Agent Workflow Architecture

This document outlines the architecture for the **Shopping Suggester** agent workflow. The system is designed to take a user's visual input (screenshot) and query, identify the product, research it across the web, and provide personalized recommendations based on user preferences.

## 1. High-Level Architecture

The core of the system is a **Multi-Agent System** orchestrated by **LangGraph**. The entire stack is **containerized with Docker** for consistency and easy deployment.

### Tech Stack Overview
- **Orchestration**: LangGraph
- **LLMs**:
  - **Vision/Parsing**: **Gemini 2.0 Flash** - Primary model for object detection and OCR.
  - **Reasoning/Analysis**: **Gemini 2.0 Flash** - Used for Market Scout, Skeptic, and detailed Analysis.
  - **Response Formatting**: **Gemini 2.0 Flash** - Fast response generation and formatting.
- **Caching**:
  - **Redis**: In-memory cache for API responses (Tavily, SerpAPI) with configurable TTL
  - **Purpose**: Reduce redundant API calls, lower latency, save costs
- **Tools**:
  - **Search**: Tavily API (General search, identifying products)
  - **Pricing**: SerpAPI (Google Shopping data)
  - **Scraping**: LangChain Web Scrapers
- **Database**: PostgreSQL (Docker container)
- **Backend & API**: FastAPI (Docker container)
- **Frontend**: React + Vite (Docker container)
- **Authentication**: Auth0

---

## 2. Docker Architecture

All services run in Docker containers managed by `docker-compose.yml`:

```
┌───────────────────────────────────────────────────────────────────┐
│                       Docker Compose                               │
├─────────────┬─────────────┬─────────────────┬─────────────────────┤
│  frontend   │   backend   │       db        │       redis         │
│ (React/Vite)│  (FastAPI)  │  (PostgreSQL)   │    (Cache Layer)    │
│  Port: 5173 │  Port: 8000 │   Port: 5433    │    Port: 6379       │
└─────────────┴─────────────┴─────────────────┴─────────────────────┘
```

### Services

| Service | Image/Build | Port | Description |
|---------|-------------|------|-------------|
| **db** | `postgres:13-alpine` | 5433:5432 | PostgreSQL database with healthcheck |
| **backend** | `./backend` | 8000:8000 | FastAPI with uvicorn, hot-reload enabled via command override |
| **frontend** | `./frontend` | 5173:5173 | Vite dev server, hot-reload enabled |
| **redis** | `redis:7-alpine` | 6379:6379 | In-memory cache for API responses |

### Running the Stack

```bash
# Start all services (rebuilds if necessary)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Environment Variables & Setup Fixes

To ensure the stack runs correctly (based on recent fixes):

1.  **Backend Configuration**:
    *   Create `backend/.env`.
    *   Required Keys: `GOOGLE_API_KEY`, `TAVILY_API_KEY`, `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`.
    *   **Fix**: `requirements.txt` must include `google-generativeai`, `langgraph`, `langchain`, `google-search-results`.

2.  **Frontend Configuration**:
    *   Create `frontend/.env`.
    *   Required Keys: `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID`, `VITE_AUTH0_AUDIENCE`, `VITE_API_URL`.

3.  **Build Optimizations**:
    *   **Frontend**: A `.dockerignore` file was added to exclude `node_modules` and `dist`. This prevents massive build contexts and significantly speeds up `docker-compose build frontend`.
    *   **Commands**: `docker-compose.yml` overrides default commands to ensure explicit host binding (`0.0.0.0`) for both FastAPI and Vite, fixing access issues from the host machine.

---

## 3. Agent Workflow (LangGraph)

The workflow is a Directed Acyclic Graph (DAG) managed by LangGraph.

### **Node 1: User Intent & Vision (The "Eye")**
*   **Input**: User uploaded image (Screenshot) + Text Prompt.
*   **Model**: **Gemini 2.0 Flash**.
*   **Responsibilities**:
    1.  **Multi-Object Detection**: Identifies **all** distinct objects/products in the image.
    2.  **Bounding Boxes**: Returns normalized coordinates [ymin, xmin, ymax, xmax] for each object.
    3.  **Context Extraction**: Reads text on screen (OCR).
*   **Output**: Structured Product Query containing a list of `detected_objects`.

### **Node 2: Discovery Layer (The "Researcher" & "Explorer")**
This phase runs two parallel agents to gather deep data.

### **Node 2a: Product Researcher (The "Deep Dive")**
*   **Input**: Structured Product Query (from Node 1).
*   **Goal**: Gather comprehensive data on the *specific* product identified.
*   **Agents**:
    *   **Search Agent**: Uses **Tavily API** to find listings.
    *   **Price Checker**: Uses **SerpAPI** for pricing.
*   **Caching**: Results cached in Redis (Tavily: 1 hour TTL, SerpAPI: 15 min TTL).

### **Node 2b: Market Scout (The "Explorer")**
*   **Input**: Structured Product Query + User Preferences.
*   **Goal**: Find relevant *alternatives* based on the user's needs.
*   **Model**: **Gemini 2.0 Flash** for fast candidate extraction.

### **Node 3: The Skeptic (Critique & Verification)**
*   **Input**: Raw product data (Main Item) + Alternative Candidates (Scout).
*   **Agent**: **Skeptic Agent** (Gemini 2.0 Flash).
*   **Responsibilities**:
    1.  **Fake Review Detection**: Analyze patterns in reviews for the main product.
    2.  **Deal Verification**: Check if the "sale price" is actually a tactic.
    3.  **Cross-Exam**: Check if the "Alternates" suggested by the Scout hold up to scrutiny.
*   **Output**: `ReviewSentiment` object.

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Contextual Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (Gemini 2.0 Flash).
*   **Logic**:
    1.  **Preference Loading**: Retrieves explicit user weights.
    2.  **Weighted Scoring**: Calculates a final match score (0-100) for each product based on price, quality, and trust.
    3.  **Ranking**: Sorts all products to determine the best recommendation.
*   **Output**: Structured Analysis Object.

### **Node 5: Response Formulation (The "Speaker")**
*   **Input**: Structured Analysis Object.
*   **Model**: **Gemini 2.0 Flash**.
*   **Responsibilities**:
    1.  **Final Recommendation**: Generate an empathetic, human-like summary.
    2.  **Data Injection**: Explicitly injects `detected_objects` and `bounding_box` data from the original state into the final JSON. This ensures the frontend has the necessary coordinates for rendering.
    3.  **Format Output**: JSON for frontend.
*   **Output**: JSON Payload.

---

## 4. Frontend Integration

### **Interactive Bounding Boxes**
The frontend (`DashboardPage.jsx`) uses the `detected_objects` list from the API response to render interactive overlays:

1.  **Rendering**: A `BoundingBoxOverlay` component is mapped over the `detected_objects` array.
2.  **Coordinates**: Gemini returns normalized coordinates (0-1000). The frontend converts these to percentage-based CSS (`top`, `left`, `width`, `height`) to overlay correctly on the responsive image.
3.  **Interaction**: Hovering over a box displays the object's name and confidence score.
4.  **Layout**: The image container uses `flex-shrink-0` to ensure it remains visible and sized correctly even when the detailed analysis results (alternatives list) expand below it.

### Recommendation Output (JSON)
The final payload sent to the frontend includes the active product data for visualization:

```json
{
  "active_product": {
    "name": "Robotic Dog",
    "bounding_box": [200, 300, 600, 700],
    "detected_objects": [
        { "name": "Robotic Dog", "bounding_box": [...], "confidence": 0.95 },
        { "name": "Remote Control", "bounding_box": [...], "confidence": 0.88 }
    ]
  },
  "outcome": "highly_recommended",
  "identified_product": "Herman Miller Aeron Chair",
  "price_analysis": { ... },
  "community_sentiment": { ... },
  "alternatives": [ ... ]
}
```

---

## 9. Model Summary (Updated)

| Node | Model | Reasoning |
|------|-------|-----------|
| **Node 1: Vision** | `gemini-2.0-flash` | Exclusive model for object detection, bounding boxes, and OCR. |
| **Node 2: Research** | N/A (API calls) | Tavily + SerpAPI, no LLM |
| **Node 2b: Market Scout** | `gemini-2.0-flash` | Fast candidate extraction from search results |
| **Node 3: Skeptic** | `gemini-2.0-flash` | Deep reasoning for fake review detection |
| **Node 4: Analysis** | `gemini-2.0-flash` | Complex multi-factor scoring and ranking |
| **Node 5: Response** | `gemini-2.0-flash` | Fast formatting and data aggregation |
