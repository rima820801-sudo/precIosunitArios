# Copilot Instructions for Precios Unitarios Web App

This document provides instructions for AI coding agents to effectively contribute to the "Precios Unitarios" codebase.

## 1. Project Overview

The project is a web application for managing construction costs, similar to the OPUS software. It's built for personal use and focuses on calculating "Unit Prices" by breaking down direct and indirect costs of construction activities.

The architecture is composed of:

-   **Backend:** A Flask/SQLAlchemy server located in the `catalogos/` directory.
-   **Frontend:** A React/Vite application located in the `frontend/` directory.
-   **Database:** An SQLite database file (`catalogos/data.sqlite3`) that is automatically created by the backend.

## 2. Developer Workflows

### Backend

To run the backend server:

1.  Navigate to the `catalogos/` directory.
2.  Create a virtual environment: `python -m venv .venv`
3.  Activate the virtual environment: `.venv\Scripts\activate`
4.  Install the dependencies: `pip install -r requirements.txt`
5.  Run the server: `python app.py`

The backend will be available at `http://localhost:8000`.

### Frontend

To run the frontend application:

1.  Navigate to the `frontend/` directory.
2.  Install the dependencies: `npm install`
3.  Run the development server: `npm run dev`

The frontend will be available at `http://localhost:3000` and will connect to the backend API.

## 3. Codebase Conventions and Patterns

### Backend (`catalogos/`)

-   **Single-File Application:** The entire backend (Flask app, SQLAlchemy models, and API endpoints) is contained within `catalogos/app.py`. There is no separate `models.py` file.
-   **SQLAlchemy Models:** Database models are defined as classes that inherit from `db.Model`. Business logic, such as calculating derived values (e.g., `fasar`), is implemented as methods within these model classes.
-   **RESTful API:** The API follows REST conventions. Endpoints are defined using Flask's `@app.route` decorator.
-   **Data Serialization:** Models have a `to_dict()` method to serialize SQLAlchemy objects into JSON-compatible dictionaries.
-   **Gemini API Integration:** The backend integrates with the Google Gemini API for AI-powered features. The API key is configured via a `.env` file in the `catalogos/` directory.

### Frontend (`frontend/`)

-   **API Client:** A custom API client using `axios` is defined in `frontend/src/api/client.ts`. The `apiFetch` function is a generic wrapper for making API requests.
-   **Component Structure:** The UI is built with React components, organized by feature under `frontend/src/components/`.
-   **Pages:** Top-level pages, corresponding to the main sections of the application, are located in `frontend/src/pages/`.

## 4. Key Files and Directories

-   `inicio de proyecto.txt`: Contains the initial project description and goals.
-   `README.md`: Provides a summary of the project, setup instructions, and API endpoint documentation.
-   `catalogos/app.py`: The core of the backend application.
-   `frontend/src/api/client.ts`: The API client for the frontend.
-   `frontend/src/pages/`: Contains the main pages of the application, which are good starting points for understanding the UI structure.
