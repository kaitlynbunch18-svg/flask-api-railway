from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import openai
import os
import requests
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

# Database model
class SupplierDeal(db.Model):
    __tablename__ = "supplier_deals"
    id = db.Column(db.String, primary_key=True)
    supplier_name = db.Column(db.String)
    subject = db.Column(db.String)
    content = db.Column(db.Text)
    ai_classification = db.Column(db.String)
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route("/api/v1/supplier-intel", methods=["POST"])
def supplier_intel():
    data = request.get_json()
    required_fields = ["supplier_name", "subject", "content"]
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    deal_id = str(uuid.uuid4())

    # Send to OpenAI for deal extraction
    try:
        prompt = f"Analyze supplier deal:\n\n{data['content']}\n\nClassify as High, Medium, or Low opportunity with confidence."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a supplier intelligence assistant."},
                      {"role": "user", "content": prompt}],
            temperature=0.2
        )
        ai_text = response["choices"][0]["message"]["content"]
    except Exception as e:
        return jsonify({"error": f"AI error: {str(e)}"}), 500

    # Optionally use Claude for a second opinion
    try:
        claude_response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-3-sonnet-20240229",
                  "max_tokens": 1024,
                  "messages": [{"role": "user", "content": f"Cross-check classification: {ai_text}"}]}
        ).json()
        claude_text = claude_response.get("content", [{}])[0].get("text", "")
    except Exception:
        claude_text = None

    # Store results
    try:
        deal = SupplierDeal(
            id=deal_id,
            supplier_name=data["supplier_name"],
            subject=data["subject"],
            content=data["content"],
            ai_classification=ai_text[:255],
            confidence=0.9  # placeholder for parsed confidence
        )
        db.session.add(deal)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "status": "success",
        "deal_id": deal_id,
        "classification": ai_text,
        "claude_check": claude_text
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
