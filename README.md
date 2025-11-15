**Healthcare Assistant Chatbot**

A simple web-based chatbot that provides general wellness advice, diet tips, and daily do’s & don’ts. This chatbot is not a substitute for professional medical advice.

**Features**

Daily do’s & don’ts suggestions
Diet tips and sample 1-day meal plans (Weight Loss, Maintenance, Muscle Gain)
Safety redirect for medical-related queries
Optional friendly AI-generated advice using OpenAI GPT (LLM)
Visible disclaimer on all responses
Basic web UI for chatting

**How to Run**

Clone or download the project:

git clone https://github.com/mohanpothula/healthcare_chatbot

**cd healthcare_chatbot**

Create a Python virtual environment and activate it:

python3 -m venv venvsource venv/bin/activate

Install dependencies:

pip install -r requirements.txt# or manually:
pip install flask openai python-dotenv
Create a .env file in the project root and add your OpenAI API key:

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
Run the app:
python app.py
Open your browser and navigate to:
http://localhost:5000
Start chatting with the bot!

**Assumptions**

The bot uses a small, keyword-based knowledge base stored in knowledge_base.json.
GPT responses are supplemental and meant for friendly advice, not medical guidance.
User queries that contain medical terms (e.g., chest pain, medication) are redirected to professional help.
The bot recognizes keywords like do, don’t, diet, weight loss, maintenance, muscle gain.

**Known Limitations**

Limited intent detection: only keyword/regex based; no ML intent recognition.
GPT fallback: may sometimes fail if the API key is incorrect, network is down, or rate limits are exceeded.
Not a medical chatbot: cannot provide diagnoses, treatment advice, or emergency instructions.
1-day diet plans only; no personalized nutrition tracking.
Web UI: very basic, shows last messages, input box, and send button.

**Example Queries**

“daily do’s” → shows daily do’s list
“daily don’ts” → shows daily don’ts list
“diet tips” → general nutrition tips
“weight loss plan” → 1-day weight loss sample meals
“tell me a joke” → fallback + GPT fun response
“I have chest pain” → safety redirect
