# legalbot
law legalbot
Constitution & Law Tutor (Classes 8–12)
=======================================

A Flask-based chatbot that answers queries about the Indian Constitution and law system. It supports scenario-based reasoning (IRAC-style), persistent chat history, feedback-driven optimization, and a clean modern UI. It also serves a precise timeline of the Constitution's history.

Quickstart
----------

1) Install deps

```
pip install -r requirements.txt
```

2) Run

```
python app.py
```

App will run on http://localhost:8000

Features
--------
- TF-IDF retrieval over a curated knowledge base in `knowledge_base/kb.json`
- Scenario handling with IRAC-style structuring
- SQLite persistence of chat history and feedback
- Feedback-improves retrieval ranking via document boosts
- Metrics endpoint with helpful rate and top referenced docs
- Attractive frontend with chat, history sidebar, export, and timeline button

Project Structure
-----------------
- `app.py` – Flask app, endpoints, retrieval, persistence
- `knowledge_base/kb.json` – curated content
- `templates/index.html` – UI skeleton
- `static/styles.css` – UI styles
- `static/app.js` – UI logic
