"""A lightweight Flask web UI for previewing message routing decisions."""

from __future__ import annotations

from flask import Flask, render_template_string, request

from src.classifier import NotificationClassifier
from src.config import AppConfig
from src.data_loader import load_all_datasets
from src.retrieval import MessageRetriever


HTML_TEMPLATE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>WhatsApp Notification Router</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7ff;
      --panel: rgba(255,255,255,0.82);
      --border: rgba(15, 23, 42, 0.08);
      --text: #0f172a;
      --muted: #64748b;
      --accent: #4f46e5;
      --accent-2: #2563eb;
      --success: #0f766e;
      --danger: #dc2626;
      --shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(79, 70, 229, 0.12), transparent 24%),
        linear-gradient(135deg, #f8fbff 0%, var(--bg) 100%);
      min-height: 100vh;
      padding: 28px;
    }
    .shell {
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
      border-radius: 28px;
      background: rgba(255,255,255,0.65);
      backdrop-filter: blur(22px);
      box-shadow: var(--shadow);
      border: 1px solid rgba(255,255,255,0.7);
    }
    .hero {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 24px;
      align-items: stretch;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(79, 70, 229, 0.14), rgba(37, 99, 235, 0.1));
      color: var(--accent);
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    h1 {
      font-size: clamp(1.9rem, 2.8vw, 2.8rem);
      margin: 14px 0 10px;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }
    .lead {
      font-size: 1rem;
      color: var(--muted);
      line-height: 1.7;
      margin: 0 0 18px;
      max-width: 620px;
    }
    .chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 20px; }
    .chip {
      display: inline-flex;
      align-items: center;
      padding: 7px 10px;
      border-radius: 999px;
      font-size: 0.9rem;
      background: #eef2ff;
      color: var(--accent);
      font-weight: 600;
    }
    form { display: flex; flex-direction: column; gap: 12px; }
    textarea {
      width: 100%;
      min-height: 140px;
      border: 1px solid rgba(99, 102, 241, 0.18);
      border-radius: 16px;
      padding: 14px 16px;
      font-size: 1rem;
      line-height: 1.6;
      color: var(--text);
      background: rgba(255,255,255,0.95);
      outline: none;
      resize: vertical;
      box-shadow: inset 0 1px 2px rgba(15,23,42,0.04);
    }
    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(79,70,229,0.12);
    }
    button {
      align-self: flex-start;
      border: none;
      border-radius: 999px;
      padding: 12px 18px;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: white;
      cursor: pointer;
      font-weight: 700;
      box-shadow: 0 12px 24px rgba(79,70,229,0.18);
      transition: transform 180ms ease, box-shadow 180ms ease;
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 16px 30px rgba(79,70,229,0.22); }
    .result {
      margin-top: 18px;
      padding: 18px;
      border-radius: 18px;
      border: 1px solid rgba(15,23,42,0.06);
      background: linear-gradient(135deg, rgba(239,246,255,0.95), rgba(224,242,254,0.85));
      animation: fadeUp 280ms ease;
    }
    .result-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
    .result-title { font-weight: 700; font-size: 1.02rem; }
    .action-pill {
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 0.84rem;
      font-weight: 700;
      text-transform: capitalize;
      background: rgba(79,70,229,0.12);
      color: var(--accent);
    }
    .meta { color: var(--muted); font-size: 0.94rem; margin-top: 8px; line-height: 1.65; }
    .preview-card {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 18px;
      background: linear-gradient(160deg, #111827 0%, #1f2937 65%, #334155 100%);
      color: white;
      overflow: hidden;
      position: relative;
    }
    .preview-card::before {
      content: \"\";
      position: absolute; inset: 0;
      background: radial-gradient(circle at top right, rgba(129,140,248,0.26), transparent 30%);
      pointer-events: none;
    }
    .preview-head { position: relative; z-index: 1; }
    .preview-title { font-size: 1.08rem; font-weight: 700; margin: 0 0 4px; }
    .preview-copy { color: rgba(255,255,255,0.74); font-size: 0.95rem; line-height: 1.6; }
    .preview-metric {
      position: relative; z-index: 1;
      display: grid; gap: 10px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .metric {
      padding: 12px;
      border-radius: 14px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
    }
    .metric strong { display: block; font-size: 1rem; margin-top: 4px; }
    .metric span { font-size: 0.78rem; color: rgba(255,255,255,0.72); text-transform: uppercase; letter-spacing: 0.08em; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 900px) {
      .hero { grid-template-columns: 1fr; }
      .preview-metric { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class=\"shell\">
    <div class=\"hero\">
      <section class=\"card\">
        <div class=\"badge\">✦ Intelligent routing assistant</div>
        <h1>Keep the right messages front and center.</h1>
        <p class=\"lead\">Preview how each WhatsApp-style message is routed into notify, digest, or mute with a clean, premium experience built for high-trust product design.</p>
        <div class=\"chip-row\">
          <span class=\"chip\">notify</span>
          <span class=\"chip\">digest</span>
          <span class=\"chip\">mute</span>
        </div>
        <form method=\"post\" action=\"/classify\">
          <textarea name=\"message_text\" placeholder=\"Type a WhatsApp-style message here…\">{{ default_message }}</textarea>
          <button type=\"submit\">Classify message</button>
        </form>
        {% if result %}
          <div class=\"result\">
            <div class=\"result-top\">
              <div class=\"result-title\">Routing result</div>
              <span class=\"action-pill\">{{ result.action }}</span>
            </div>
            <div class=\"meta\"><strong>Message Type:</strong> {{ result.message_type }}</div>
            <div class=\"meta\"><strong>Reason:</strong> {{ result.reason }}</div>
            <div class=\"meta\"><strong>Confidence:</strong> {{ result.confidence }}</div>
            <div class=\"meta\"><strong>Evidence:</strong> {{ result.evidence_message_ids }}</div>
          </div>
        {% endif %}
      </section>
      <aside class=\"card preview-card\">
        <div class=\"preview-head\">
          <div class=\"badge\" style=\"background: rgba(255,255,255,0.12); color: white;\">Live preview</div>
          <h2 class=\"preview-title\" style=\"margin-top: 12px;\">Designed for calm, clear decisions</h2>
          <p class=\"preview-copy\">Each message receives a thoughtful priority signal, so the experience feels intentional rather than noisy.</p>
        </div>
        <div class=\"preview-metric\">
          <div class=\"metric\"><span>Priority</span><strong>Adaptive</strong></div>
          <div class=\"metric\"><span>Signal</span><strong>Contextual</strong></div>
          <div class=\"metric\"><span>Experience</span><strong>Minimal</strong></div>
        </div>
      </aside>
    </div>
  </div>
</body>
</html>
"""


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)

    config = AppConfig.from_environment()
    datasets = load_all_datasets(config.dataset_dir)
    history = datasets.get("message_history.csv")
    retriever = MessageRetriever(history if history is not None else None)
    classifier = NotificationClassifier()

    @app.get("/")
    def home() -> str:
        return render_template_string(HTML_TEMPLATE, default_message="Meeting starts at 10 AM. Please join ASAP.", result=None)

    @app.post("/classify")
    def classify() -> str:
        message_text = request.form.get("message_text", "")
        message = {"message_text": message_text}
        evidence_ids = retriever.find_similar_messages(message)
        prediction = classifier.classify_message(message, evidence_ids, {})
        return render_template_string(
            HTML_TEMPLATE,
            default_message=message_text,
            result=prediction,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
