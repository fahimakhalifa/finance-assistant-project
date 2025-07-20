# Finance Assistant App

An interactive AI-powered personal finance assistant built with **Streamlit**.  
It helps users **forecast spending**, **track budgets**, **analyze goals**, and even **chat with an AI assistant** to get insights from their financial behavior.

---

## Features

- Forecast spending per category using XGBoost
- AI Chatbot assistant (via Mistral/Ollama)
- Monthly goal tracking
- Dynamic feedback on budgeting
- Export PDF reports
- Add and edit new records easily

---

## Screenshots

> Add these to show the app in action:
- `images`

```
📁 finance-assistant/
├── app/
│   ├── main.py
│   ├── overview_tab.py
│   ├── chatbot_tab.py
│   ├── budgeting_tab.py
│   └── ...
├── core/
├── utils/
├── model/
├── images/      
│   ├── overview.png
│   └── chatbot.png
├── requirements.txt
└── README.md
```

## How to Run

```bash
pip install -r requirements.txt
streamlit run app/main.py
```
⚠️ To use the chatbot feature, open utils/llm.py and replace the placeholder with your own Ollama API key. The chatbot will not work without it.

## Requirements

Install all dependencies:

```bash
pip install -r requirements.txt
```


