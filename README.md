# WildCatter Property AI MVP

Confidential internship-assignment prototype. Do not publish or redistribute without permission.

## Features
- Natural-language property search
- Voice input using browser Speech Recognition where supported
- AI-style intent extraction into structured filters
- Mumbai/Lokhandwala sample project dataset
- Interactive Uber-style map using Leaflet + OpenStreetMap
- Developer score
- Buyer/Broker dashboard with search history and enquiries
- Developer dashboard with project interest
- SQLite central data store
- REST API through FastAPI

## Run on Windows

1. Open PowerShell in this folder.
2. Create a virtual environment:
   `python -m venv venv`
3. Activate:
   `venv\Scripts\activate`
4. Install:
   `pip install -r requirements.txt`
5. Start:
   `uvicorn app.main:app --reload`
6. Open:
   `http://127.0.0.1:8000`

## Demo query

"Show me all residential projects of 2 bedroom that cost below Rs 8 crore and are in Lokhandwala and get completed by June 2027."

The prototype converts this into filters and searches the local normalized property dataset.

## Data note

The included projects are demo/seed data for the MVP. They are not presented as a live or exhaustive MahaRERA dataset. A production ingestion agent should collect and normalize current MahaRERA project data with appropriate permission and compliance.
