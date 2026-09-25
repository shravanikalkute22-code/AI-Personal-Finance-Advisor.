import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), default="")
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_user():
    user = User.query.get(session.get("user_id")) if session.get("user_id") else None
    return {"current_user": user}

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter all details. Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "error")
            return redirect(url_for("register"))
        user = User(name=name, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    incomes = Income.query.filter_by(user_id=uid).all()
    expenses = Expense.query.filter_by(user_id=uid).all()
    budgets = Budget.query.filter_by(user_id=uid).all()
    total_income = sum(x.amount for x in incomes)
    total_expense = sum(x.amount for x in expenses)
    savings = total_income - total_expense
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount
    budget_total = sum(b.amount for b in budgets)
    return render_template("dashboard.html", total_income=total_income,
                           total_expense=total_expense, savings=savings,
                           categories=categories, budget_total=budget_total,
                           expenses=expenses[-8:][::-1])

@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            if amount <= 0: raise ValueError
            db.session.add(Income(user_id=session["user_id"],
                                  source=request.form["source"].strip(),
                                  amount=amount))
            db.session.commit()
            flash("Income added.", "success")
        except (ValueError, KeyError):
            flash("Enter a valid positive amount.", "error")
        return redirect(url_for("income"))
    records = Income.query.filter_by(user_id=session["user_id"]).order_by(Income.date.desc()).all()
    return render_template("income.html", records=records)

@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    categories = ["Food", "Travel", "Shopping", "Education", "Bills", "Entertainment", "Health", "Other"]
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            if amount <= 0: raise ValueError
            db.session.add(Expense(user_id=session["user_id"],
                                    category=request.form["category"],
                                    description=request.form.get("description", "").strip(),
                                    amount=amount))
            db.session.commit()
            flash("Expense added.", "success")
        except (ValueError, KeyError):
            flash("Enter a valid positive amount.", "error")
        return redirect(url_for("expenses"))
    records = Expense.query.filter_by(user_id=session["user_id"]).order_by(Expense.date.desc()).all()
    return render_template("expenses.html", records=records, categories=categories)

@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    categories = ["Food", "Travel", "Shopping", "Education", "Bills", "Entertainment", "Health", "Other"]
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            if amount <= 0: raise ValueError
            db.session.add(Budget(user_id=session["user_id"],
                                  category=request.form["category"], amount=amount))
            db.session.commit()
            flash("Budget added.", "success")
        except (ValueError, KeyError):
            flash("Enter a valid positive amount.", "error")
        return redirect(url_for("budget"))
    records = Budget.query.filter_by(user_id=session["user_id"]).all()
    return render_template("budget.html", records=records, categories=categories)

@app.route("/ai-advisor")
@login_required
def ai_advisor():
    uid = session["user_id"]
    incomes = Income.query.filter_by(user_id=uid).all()
    expenses = Expense.query.filter_by(user_id=uid).all()
    total_income = sum(x.amount for x in incomes)
    total_expense = sum(x.amount for x in expenses)
    savings = total_income - total_expense
    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
    top_category = max(by_cat, key=by_cat.get) if by_cat else "None"
    rate = (savings / total_income * 100) if total_income else 0

    recommendations = []
    if total_income == 0:
        recommendations.append("Add your monthly income to generate a more useful financial plan.")
    elif total_expense > total_income:
        recommendations.append("Your recorded expenses are higher than your income. Review non-essential spending first.")
    else:
        recommendations.append(f"Your current recorded savings are ₹{savings:,.2f}. Keep tracking every transaction.")
    if by_cat:
        recommendations.append(f"Your highest expense category is {top_category} (₹{by_cat[top_category]:,.2f}). Check whether some spending can be reduced.")
    if rate < 10 and total_income > 0:
        recommendations.append("Your current recorded savings rate is below 10%. Consider setting a small automatic savings target.")
    elif rate >= 20:
        recommendations.append("Your recorded savings rate is 20% or more. Consider building an emergency fund before increasing discretionary spending.")
    recommendations.append("Keep an emergency fund target based on your essential monthly expenses.")
    return render_template("ai_advisor.html", total_income=total_income,
                           total_expense=total_expense, savings=savings,
                           rate=rate, top_category=top_category,
                           recommendations=recommendations)

@app.route("/api/summary")
@login_required
def api_summary():
    uid = session["user_id"]
    incomes = Income.query.filter_by(user_id=uid).all()
    expenses = Expense.query.filter_by(user_id=uid).all()
    return jsonify({
        "income": round(sum(x.amount for x in incomes), 2),
        "expense": round(sum(x.amount for x in expenses), 2),
        "savings": round(sum(x.amount for x in incomes) - sum(x.amount for x in expenses), 2)
    })

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
