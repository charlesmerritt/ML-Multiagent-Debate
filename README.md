# ML-Multiagent-Debate

This project demonstrates a **multi-agent debate** approach using the **OpenAI Chat API**. It has three main pages:

1. **Home** – A simple welcome page with links to the other pages.
2. **Legal** – Demonstrates a “one-shot” approach to a legal question and a multi-round debate approach that collects Agent 1, Agent 2, and a Moderator’s consensus in each round.
3. **Math** – Same structure as the legal page, but for a math question.

Each of the **Legal** and **Math** pages is split into two sections:
- **One-Shot Approach** – A single query to the OpenAI API returning a concise answer.
- **Debate Approach** – A multi-round process where two agents respond, and a moderator then synthesizes a consensus. The final consensus from each round becomes the next round’s “question,” culminating in a final answer.

### Prerequisites

- **Node.js** (v14+ recommended)
- **npm** (Node Package Manager)
- A valid **OpenAI API Key**

### Setup Instructions

1. **Clone or Download** this repository to your local machine.

2. **Navigate** to the project folder in your terminal:
   ```bash
   cd ML-Multiagent-Debate
Initialize a package.json if one doesn’t exist (only if you haven’t already):

bash
Copy
npm init -y
This creates a basic package.json file.

Install Dependencies:

bash
Copy
npm install express dotenv
express is the web framework used
dotenv loads environment variables (like your API key)
Create a .env File in the project root with your OpenAI API key:

plaintext
Copy
OPENAI_API_KEY=your_openai_api_key_here
Run the Server:

bash
Copy
node server.js
The server will start on http://localhost:3000.

Usage
Home Page:
Access http://localhost:3000/. From here, click on Legal or Math.

Legal Page:

Click Get Zero-Shot Answer to see a concise single response to the legal question.
Enter the number of rounds in the Number of Rounds input and click Start Debate to see each round’s Agent 1, Agent 2, and Moderator responses. Finally, a “Final Synthesis” is displayed at the bottom.
Math Page:

Same flow as the legal page, but for a math problem.
Commands Summary
npm init -y
Creates a default package.json if you don’t have one.

npm install
Installs dependencies (like Express, dotenv).

node server.js
Starts the Express server on port 3000.

Environment Variables
Create a .env file in the root of the project with the following content:

plaintext
Copy
OPENAI_API_KEY=your_openai_api_key_here
Replace your_openai_api_key_here with your actual API key from the OpenAI dashboard.
