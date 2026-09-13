# Setup Guide

This guide explains how to install and run the RouteWise AI demo on your local machine.

## Prerequisites
- Python 3.9 or higher installed
- Git installed
- Terminal / Command Prompt

## Environment Variables
We have provided an `.env.example` file in the `src/` directory. For this local demo, no external secret keys are required as the data is mocked for the presentation.

## Exact Install Commands
Open your terminal and run the following commands:

1. Clone the repository and navigate to the source folder:
```bash
git clone https://github.com/[YOUR-USERNAME]/bob-ai-hackathon-[YOUR-TEAM-NAME].git
cd bob-ai-hackathon-[YOUR-TEAM-NAME]/src
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
- **Windows:** `.venv\Scripts\activate`
- **macOS/Linux:** `source .venv/bin/activate`

4. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Exact Run Commands
Once installed and activated, start the web application:
```bash
streamlit run app.py
```

## How to Verify It's Working
1. Your terminal should output a local URL, typically `http://localhost:8501`.
2. Open that URL in your web browser.
3. You should see the RouteWise AI dashboard with the simulated map.
4. Type a query in the left sidebar (e.g., "How does the storm affect us?") and click **Ask Bob** to verify the AI assistant responds.

## Troubleshooting

| Error | Cause & Solution |
|-------|------------------|
| `streamlit is not recognized as an internal or external command` | The virtual environment is not activated, or you forgot to run `pip install -r requirements.txt`. |
| Port 8501 is already in use | Run `streamlit run app.py --server.port 8502` to force a different port. |
