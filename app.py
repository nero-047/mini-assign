import os
from flask import Flask, request, jsonify, render_template
from services.translator import translate_text
from services.currency import convert_currency
from services.portfolio import resume_to_portfolio
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html", title="AI Tools Hub")


# ---------------- Translator ---------------- #
@app.route("/translate", methods=["GET", "POST"])
def translate():
    if request.method == "POST":
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "No text provided"}), 400

        text = data["text"]
        dest = data.get("dest", "en")
        result = translate_text(text, dest)
        return jsonify(result)
    
    return render_template("translate.html", title="Translator")


# ---------------- Currency Converter ---------------- #
@app.route("/currency", methods=["GET", "POST"])
def currency():
    if request.method == "POST":
        data = request.get_json()
        if not data or "amount" not in data:
            return jsonify({"error": "Missing parameters"}), 400

        try:
            amount = float(data["amount"])
        except ValueError:
            return jsonify({"error": "Amount must be numeric"}), 400

        from_currency = data.get("from", "USD")
        to_currency = data.get("to", "INR")
        result = convert_currency(amount, from_currency, to_currency)
        return jsonify(result)

    return render_template("currency.html", title="Currency Converter")


# ---------------- Resume → Portfolio ---------------- #
@app.route("/portfolio", methods=["GET", "POST"])
def portfolio():
    if request.method == "POST":
        try:
            if "file" not in request.files:
                return jsonify({"error": "No file uploaded"}), 400

            file = request.files["file"]
            if not file or file.filename.strip() == "":
                return jsonify({"error": "Empty filename"}), 400

            save_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(save_path)

            portfolio_data = resume_to_portfolio(save_path)

            if not portfolio_data or "error" in portfolio_data:
                return jsonify({"error": "Could not parse resume"}), 500

            return jsonify(portfolio_data)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template("portfolio.html", title="Resume → Portfolio")


if __name__ == "__main__":
    app.run(debug=True)