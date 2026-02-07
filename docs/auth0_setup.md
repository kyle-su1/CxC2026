# Auth0 Setup Guide

To enable authentication for your application, you need to configure Auth0.

## 1. Create an Auth0 Account
Go to [Auth0.com](https://auth0.com/) and sign up for a free account.

## 2. Configure the Frontend (Single Page Application)
1.  **Create Application**:
    *   In the Auth0 Dashboard, go to **Applications** > **Applications**.
    *   Click **Create Application**.
    *   Name it "Shopping Suggester Frontend".
    *   Select **Single Page Web Applications**.
    *   Click **Create**.
2.  **Settings**:
    *   Go to the **Settings** tab.
    *   **Allowed Callback URLs**: `http://localhost:5173`
    *   **Allowed Logout URLs**: `http://localhost:5173`
    *   **Allowed Web Origins**: `http://localhost:5173`
    *   Scroll down and click **Save Changes**.
3.  **Get Credentials**:
    *   Copy **Domain** and **Client ID** from the Settings page.
    *   Paste them into `frontend/.env`:
        ```
        VITE_AUTH0_DOMAIN=your-domain.us.auth0.com
        VITE_AUTH0_CLIENT_ID=your-client-id
        ```

## 3. Configure the Backend (API)
1.  **Create API**:
    *   Go to **Applications** > **APIs**.
    *   Click **Create API**.
    *   **Name**: "Shopping Suggester API".
    *   **Identifier**: `https://shopping-suggester-api` (or any URL you prefer). This will be your **Audience**.
    *   Click **Create**.
2.  **Get Credentials**:
    *   The **Identifier** is your `AUTH0_API_AUDIENCE`.
    *   The **Domain** is the same as the frontend (found in key settings or the test tab).
3.  **Update Backend Env**:
    *   Paste them into `.env` (in the root directory):
        ```
        AUTH0_DOMAIN=your-domain.us.auth0.com
        AUTH0_API_AUDIENCE=https://shopping-suggester-api
        AUTH0_ALGORITHM=RS256
        ```
    *   Also update `frontend/.env` with the audience:
        ```
        VITE_AUTH0_AUDIENCE=https://shopping-suggester-api
        ```

## 4. Run the App
1.  Restart the backend: `docker compose restart backend`
2.  Restart the frontend: `npm run dev` in `frontend/` directory.
