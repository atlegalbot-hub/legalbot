import os
import json
import time
import uuid
import re
import sqlite3
from datetime import timedelta

from flask import Flask, request, jsonify, render_template, session, g
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "chat.db")
KB_PATH = os.path.join(APP_DIR, "knowledge_base", "kb.json")


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")
    app.permanent_session_lifetime = timedelta(days=365)

    # --- Database helpers ---
    def get_db():
        if "db" not in g:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db

    @app.teardown_appcontext
    def close_connection(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_message TEXT NOT NULL,
                sources TEXT NOT NULL,
                response_time_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_chats_session ON chats(session_id);

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(chat_id) REFERENCES chats(id)
            );

            CREATE TABLE IF NOT EXISTS doc_boosts (
                doc_id TEXT PRIMARY KEY,
                boost REAL NOT NULL DEFAULT 0.0,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        db.commit()

    # --- Knowledge base and retrieval ---
    if not os.path.exists(KB_PATH):
        raise FileNotFoundError(f"Knowledge base not found at {KB_PATH}")

    with open(KB_PATH, "r", encoding="utf-8") as f:
        kb_docs = json.load(f)

    # Ensure each doc has required fields
    for doc in kb_docs:
        for key in ["id", "title", "section", "content"]:
            if key not in doc:
                raise ValueError(f"KB document missing '{key}': {doc}")
        if "tags" not in doc:
            doc["tags"] = []

    corpus = [
        f"{d['title']}\n{d['section']}\n{' '.join(d.get('tags', []))}\n{d['content']}"
        for d in kb_docs
    ]
    doc_id_to_index = {d["id"]: i for i, d in enumerate(kb_docs)}
    index_to_doc = {i: d for i, d in enumerate(kb_docs)}

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        max_df=0.9,
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Precompute IDF mapping for sentence scoring
    vocabulary = vectorizer.vocabulary_
    idf_array = vectorizer.idf_
    idf_by_term = {term: float(idf_array[idx]) for term, idx in vocabulary.items()}

    def ensure_session():
        if "session_id" not in session:
            session["session_id"] = str(uuid.uuid4())
        return session["session_id"]

    def split_sentences(text):
        # Basic sentence splitter; avoids heavy dependencies
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", text.strip())
        return [p.strip() for p in parts if p.strip()]

    def get_doc_boosts(doc_indices):
        if not doc_indices:
            return {}
        db = get_db()
        placeholders = ",".join(["?"] * len(doc_indices))
        doc_ids = [index_to_doc[i]["id"] for i in doc_indices]
        rows = db.execute(
            f"SELECT doc_id, boost FROM doc_boosts WHERE doc_id IN ({placeholders})",
            doc_ids,
        ).fetchall()
        boosts = {row["doc_id"]: float(row["boost"]) for row in rows}
        return boosts

    def update_doc_boosts(doc_ids, delta):
        db = get_db()
        for doc_id in doc_ids:
            db.execute(
                """
                INSERT INTO doc_boosts(doc_id, boost, updated_at)
                VALUES(?, ?, datetime('now'))
                ON CONFLICT(doc_id) DO UPDATE SET
                    boost = boost + excluded.boost,
                    updated_at = datetime('now')
                """,
                (doc_id, float(delta)),
            )
        db.commit()

    def retrieve(query_text, top_k=5):
        query_vec = vectorizer.transform([query_text])
        cosine_scores = linear_kernel(query_vec, tfidf_matrix).ravel()
        # Apply boosts
        top_indices = cosine_scores.argsort()[::-1][:max(top_k * 3, 10)]
        boosts_map = get_doc_boosts(top_indices)
        adjusted_scores = []
        for idx in top_indices:
            doc = index_to_doc[idx]
            boost = float(boosts_map.get(doc["id"], 0.0))
            adjusted_scores.append((idx, float(cosine_scores[idx] + 0.15 * boost)))
        adjusted_scores.sort(key=lambda x: x[1], reverse=True)
        top = adjusted_scores[:top_k]
        return [(index_to_doc[i], score) for i, score in top]

    def build_irac_answer(user_query, retrieved_docs):
        # Extract top sentences relevant to the query from top documents
        query_vec = vectorizer.transform([user_query])
        selected_sentences = []
        candidate_sentences = []
        for doc, score in retrieved_docs:
            sentences = split_sentences(doc["content"])[:12]
            for sent in sentences:
                if len(sent) < 20:
                    continue
                sent_vec = vectorizer.transform([sent])
                sim = float(linear_kernel(query_vec, sent_vec).ravel()[0])
                candidate_sentences.append((sent, sim, doc))
        # pick top unique sentences
        candidate_sentences.sort(key=lambda x: x[1], reverse=True)
        used = set()
        for sent, sim, doc in candidate_sentences:
            key = sent[:80]
            if key in used:
                continue
            selected_sentences.append((sent, doc))
            used.add(key)
            if len(selected_sentences) >= 6:
                break

        # Build IRAC structure
        issue = user_query.strip()

        # Rule: synthesize short bullets from selected sentences mentioning Articles/Parts
        def short_rule(text):
            text = re.sub(r"\s+", " ", text)
            return text

        rules = []
        for sent, doc in selected_sentences[:3]:
            rules.append(f"{short_rule(sent)}")

        applications = []
        for sent, doc in selected_sentences[3:]:
            applications.append(sent)

        conclusion = "In summary, apply the cited Articles and principles to the facts: check which rights are engaged, applicable reasonable restrictions, and any relevant Supreme Court precedents."

        answer_lines = []
        answer_lines.append("Issue: " + issue)
        if rules:
            answer_lines.append("\nRule:")
            for r in rules:
                answer_lines.append(f"- {r}")
        if applications:
            answer_lines.append("\nApplication:")
            for a in applications:
                answer_lines.append(f"- {a}")
        answer_lines.append("\nConclusion: " + conclusion)
        return "\n".join(answer_lines)

    def build_direct_answer(user_query, retrieved_docs):
        # Concise synthesis: first 3-4 high-similarity sentences across top docs
        query_vec = vectorizer.transform([user_query])
        candidate = []
        for doc, score in retrieved_docs:
            for sent in split_sentences(doc["content"])[:10]:
                if len(sent) < 20:
                    continue
                svec = vectorizer.transform([sent])
                sim = float(linear_kernel(query_vec, svec).ravel()[0])
                candidate.append((sim, sent, doc))
        candidate.sort(key=lambda x: x[0], reverse=True)
        top_sents = []
        used = set()
        for sim, sent, doc in candidate:
            key = sent[:80]
            if key in used:
                continue
            top_sents.append((sent, doc))
            used.add(key)
            if len(top_sents) >= 4:
                break
        synthesis = " ".join([s for s, _ in top_sents])
        return synthesis if synthesis else "I could not find an exact match. Please rephrase your question with specific Articles or topics."

    def format_answer(user_query, retrieved_docs):
        scenario_markers = [
            "scenario",
            "case",
            "suppose",
            "if ",
            "what should",
            "how should",
        ]
        is_scenario = any(m in user_query.lower() for m in scenario_markers)
        if is_scenario:
            body = build_irac_answer(user_query, retrieved_docs)
        else:
            body = build_direct_answer(user_query, retrieved_docs)

        # Add systematic footer with sources
        sources = [
            {
                "id": d["id"],
                "title": d["title"],
                "section": d["section"],
            }
            for d, _ in retrieved_docs
        ]

        footer_lines = ["\n\nSources:"]
        for s in sources:
            footer_lines.append(f"- {s['title']} ({s['section']}) [id: {s['id']}]")
        return body + "\n" + "\n".join(footer_lines), sources

    @app.before_request
    def assign_session():
        ensure_session()
        session.permanent = True

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        payload = request.get_json(force=True)
        user_message = (payload.get("message") or "").strip()
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        start = time.time()

        retrieved = retrieve(user_message, top_k=5)
        answer, sources = format_answer(user_message, retrieved)
        duration_ms = int((time.time() - start) * 1000)

        # Persist chat
        db = get_db()
        cur = db.execute(
            "INSERT INTO chats(session_id, user_message, bot_message, sources, response_time_ms) VALUES (?, ?, ?, ?, ?)",
            (session["session_id"], user_message, answer, json.dumps(sources), duration_ms),
        )
        db.commit()
        chat_id = cur.lastrowid

        return jsonify({
            "chat_id": chat_id,
            "answer": answer,
            "sources": sources,
            "response_time_ms": duration_ms,
        })

    @app.route("/api/history", methods=["GET"])
    def api_history():
        limit = int(request.args.get("limit", 50))
        db = get_db()
        rows = db.execute(
            "SELECT id, user_message, bot_message, sources, response_time_ms, created_at FROM chats WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session["session_id"], limit),
        ).fetchall()
        history = []
        for r in rows:
            history.append({
                "id": r["id"],
                "user_message": r["user_message"],
                "bot_message": r["bot_message"],
                "sources": json.loads(r["sources"] or "[]"),
                "response_time_ms": r["response_time_ms"],
                "created_at": r["created_at"],
            })
        return jsonify({"history": history[::-1]})

    @app.route("/api/feedback", methods=["POST"])
    def api_feedback():
        payload = request.get_json(force=True)
        chat_id = payload.get("chat_id")
        rating = int(payload.get("rating", 0))  # 1 or -1
        comment = (payload.get("comment") or "").strip()
        if rating not in (-1, 1):
            return jsonify({"error": "rating must be 1 or -1"}), 400
        db = get_db()
        row = db.execute("SELECT sources FROM chats WHERE id = ? AND session_id = ?", (chat_id, session["session_id"])) .fetchone()
        if not row:
            return jsonify({"error": "chat not found"}), 404
        db.execute(
            "INSERT INTO feedback(chat_id, rating, comment) VALUES (?, ?, ?)",
            (chat_id, rating, comment or None),
        )
        db.commit()
        # Update boosts for the documents used in this chat
        try:
            sources = json.loads(row["sources"] or "[]")
            doc_ids = [s["id"] for s in sources]
            update_doc_boosts(doc_ids, 0.2 * float(rating))
        except Exception:
            pass
        return jsonify({"ok": True})

    @app.route("/api/constitution_history", methods=["GET"])
    def api_constitution_history():
        # Return the curated, precise timeline from the KB
        history_doc = next((d for d in kb_docs if d.get("id") == "HISTORY_TIMELINE"), None)
        if not history_doc:
            return jsonify({"error": "history not found"}), 404
        return jsonify({
            "title": history_doc["title"],
            "section": history_doc["section"],
            "content": history_doc["content"],
            "tags": history_doc.get("tags", []),
        })

    @app.route("/api/metrics", methods=["GET"])
    def api_metrics():
        db = get_db()
        total_chats = db.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
        avg_ms_row = db.execute("SELECT AVG(response_time_ms) FROM chats").fetchone()[0]
        avg_ms = int(avg_ms_row) if avg_ms_row is not None else 0
        fb_rows = db.execute("SELECT rating, COUNT(*) AS c FROM feedback GROUP BY rating").fetchall()
        helpful = sum(r["c"] for r in fb_rows if r["rating"] == 1)
        rated = sum(r["c"] for r in fb_rows)
        helpful_rate = (helpful / rated) if rated else 0.0

        # Top referenced docs by chats
        rows = db.execute("SELECT sources FROM chats").fetchall()
        doc_counts = {}
        for r in rows:
            try:
                srcs = json.loads(r["sources"] or "[]")
                for s in srcs:
                    doc_counts[s["id"]] = doc_counts.get(s["id"], 0) + 1
            except Exception:
                continue
        top_docs = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_docs = [
            {
                "id": doc_id,
                "title": next((d["title"] for d in kb_docs if d["id"] == doc_id), doc_id),
                "count": count,
            }
            for doc_id, count in top_docs
        ]

        return jsonify({
            "total_chats": total_chats,
            "avg_response_time_ms": avg_ms,
            "helpful_rate": helpful_rate,
            "top_docs": top_docs,
        })

    # Initialize DB on startup
    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)

