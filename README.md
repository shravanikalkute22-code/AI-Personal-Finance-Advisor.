# AI Personal Finance Advisor

A beginner-friendly full-stack Flask project for an AI-powered personal finance management course/demo.

## Features
- User registration and login
- Password hashing and protected routes
- Income tracking
- Expense tracking with categories
- Budget planning
- Dashboard with income, expenses and savings
- Category-wise spending analysis
- AI-style personalized financial recommendations
- JSON summary API
- SQLite database
- `.env` configuration
- Responsive UI

## Run locally

### Windows
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open: http://127.0.0.1:5000

### Demo flow
1. Register a new account.
2. Login.
3. Add income.
4. Add several expenses.
5. Add a budget.
6. Open Dashboard.
7. Open AI Advisor.

## Important
The included AI Advisor is a deterministic demo recommendation engine, so the project works without an API key. For a course requirement that explicitly requires ChatGPT/Gemini API integration, connect an approved provider using an environment variable and never commit the API key to GitHub.

## GitHub
```bash
git init
git add .
git commit -m "AI Personal Finance Advisor"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Ngrok demo
After the Flask app is running locally, expose port 5000 with your installed ngrok client:
```bash
ngrok http 5000
```
Use the generated HTTPS URL for a temporary demo. Do not put secrets in the repository.
