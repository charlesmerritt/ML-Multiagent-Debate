require('dotenv').config();
const express = require('express');
const app = express();
const port = 3000;

// Built-in body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public')); // optional, for serving static files (CSS/JS)

const API_KEY = process.env.OPENAI_API_KEY;
const API_URL = "https://api.openai.com/v1/chat/completions";
const MODEL = "gpt-3.5-turbo";

// ========== One-Shot (Zero-Shot) Answer Function ==========
async function getZeroShotResponse(query) {
  const messages = [
    { role: "user", content: `Question: ${query}\nProvide a clear and concise answer.` }
  ];
  const data = {
    model: MODEL,
    messages,
    max_tokens: 150,
    temperature: 0.7
  };

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
    }
    const json = await response.json();
    const answer = json.choices[0].message.content.trim();
    return answer;
  } catch (error) {
    console.error("Error in getZeroShotResponse:", error);
    return "Error retrieving answer.";
  }
}

// ========== Multiagent Debate Function (Round-by-Round) ==========
async function multiagentDebate(query, rounds = 1) {
  // We'll store the data for each round here:
  const roundData = [];

  let currentQuery = query;       // The question or the last consensus
  let consensusAnswer = "";       // The final synthesis after each round

  for (let i = 0; i < rounds; i++) {
    try {
      // -------- Agent 1's detailed answer --------
      const agent1Messages = [
        { role: "user", content: `Question: ${currentQuery}\nProvide a detailed answer.` }
      ];
      const agent1Response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`
        },
        body: JSON.stringify({
          model: MODEL,
          messages: agent1Messages,
          max_tokens: 200,
          temperature: 0.7
        })
      });
      const agent1Json = await agent1Response.json();
      const agent1Answer = agent1Json.choices[0].message.content.trim();

      // -------- Agent 2's detailed answer --------
      const agent2Messages = [
        { role: "user", content: `Question: ${currentQuery}\nProvide a detailed answer.` }
      ];
      const agent2Response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`
        },
        body: JSON.stringify({
          model: MODEL,
          messages: agent2Messages,
          max_tokens: 200,
          temperature: 0.7
        })
      });
      const agent2Json = await agent2Response.json();
      const agent2Answer = agent2Json.choices[0].message.content.trim();

      // -------- Moderator / Debate Step --------
      const debateMessages = [
        { role: "system", content: "You are an AI debate moderator. Analyze the two responses and provide a consensus answer that corrects any errors." },
        { role: "user", content: `Agent 1: ${agent1Answer}\nAgent 2: ${agent2Answer}\n\nBased on these responses, provide a final consensus answer for the question: ${currentQuery}` }
      ];
      
      const debateResponse = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`
        },
        body: JSON.stringify({
          model: MODEL,
          messages: debateMessages,
          max_tokens: 200,
          temperature: 0.7
        })
      });
      const debateJson = await debateResponse.json();
      consensusAnswer = debateJson.choices[0].message.content.trim();

      // Store this round’s data so we can display it in the UI
      roundData.push({
        roundNumber: i + 1,
        agent1Answer,
        agent2Answer,
        moderatorAnswer: consensusAnswer
      });

      // The consensus from this round becomes the next "query" to refine
      currentQuery = consensusAnswer;

    } catch (error) {
      console.error("Error in multiagentDebate:", error);
      return {
        roundData,
        finalAnswer: "Error during debate process."
      };
    }
  }

  // Return the entire array of round data plus the final answer
  return {
    roundData,
    finalAnswer: consensusAnswer
  };
}

// ========== Sample Queries for the 2 Pages ==========
const legalQuery = "How might the interpretation of the Fourth Amendment adapt to modern surveillance challenges?";
const mathQuery = "Given a rectangle whose length is three times its width and whose perimeter is 64 units, what is its area?";

// ========== Express Routes ==========

// ---------- Home Page ----------
app.get('/', (req, res) => {
  res.send(`
  <!DOCTYPE html>
  <html>
    <head>
      <title>Home</title>
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
      <div class="container mt-4">
        <h1>Welcome</h1>
        <p>Select a use case:</p>
        <ul>
          <li><a href="/legal">Legal Use Case</a></li>
          <li><a href="/math">Math Question</a></li>
        </ul>
      </div>
    </body>
  </html>
  `);
});

// ---------- Legal Page ----------
app.get('/legal', (req, res) => {
  res.send(`
  <!DOCTYPE html>
  <html>
  <head>
    <title>Legal Use Case</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
      .section { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }
      .round-section { background: #f9f9f9; padding: 10px; margin: 10px 0; }
      .round-title { font-weight: bold; }
      .final-answer { background: #e1ffe1; padding: 10px; margin-top: 20px; border: 1px solid #bbb; }
    </style>
  </head>
  <body>
    <div class="container">
      <nav class="mt-3">
        <a href="/">Home</a> | <a href="/legal">Legal</a> | <a href="/math">Math</a>
      </nav>
      <h1 class="mt-4">Legal Use Case</h1>
      <div class="row">
        <!-- One-Shot Section -->
        <div class="col-md-6 section">
          <h3>One-Shot Approach</h3>
          <p><strong>Question:</strong> ${legalQuery}</p>
          <button id="oneShotBtn" class="btn btn-primary">Get Zero-Shot Answer</button>
          <div id="oneShotResult" class="mt-3"></div>
        </div>
        <!-- Debate Section -->
        <div class="col-md-6 section">
          <h3>Debate Approach</h3>
          <p><strong>Question:</strong> ${legalQuery}</p>
          <div class="form-group">
            <label for="roundsInput">Number of Rounds:</label>
            <input type="number" id="roundsInput" class="form-control" value="1" min="1">
          </div>
          <button id="debateBtn" class="btn btn-secondary">Start Debate</button>
          <div id="debateRounds" class="mt-3"></div>
          <div id="debateFinal" class="final-answer"></div>
        </div>
      </div>
    </div>

    <script>
      document.getElementById('oneShotBtn').addEventListener('click', async () => {
        document.getElementById('oneShotResult').innerText = "Loading...";
        const response = await fetch('/api/legal/one-shot', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        document.getElementById('oneShotResult').innerText = data.answer;
      });

      document.getElementById('debateBtn').addEventListener('click', async () => {
        const rounds = document.getElementById('roundsInput').value;
        document.getElementById('debateRounds').innerHTML = "Loading...";
        document.getElementById('debateFinal').innerHTML = "";

        const response = await fetch('/api/legal/debate', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rounds: rounds })
        });
        const data = await response.json();

        // Clear the placeholder
        document.getElementById('debateRounds').innerHTML = "";
        
        // Display each round’s data
        data.roundData.forEach(round => {
          const roundDiv = document.createElement('div');
          roundDiv.classList.add('round-section');
          roundDiv.innerHTML = \`
            <div class="round-title">Round \${round.roundNumber}</div>
            <p><strong>Agent 1:</strong> \${round.agent1Answer}</p>
            <p><strong>Agent 2:</strong> \${round.agent2Answer}</p>
            <p><strong>Moderator:</strong> \${round.moderatorAnswer}</p>
          \`;
          document.getElementById('debateRounds').appendChild(roundDiv);
        });

        // Show final synthesis at the bottom
        const finalAnswer = data.finalAnswer || "No final answer returned.";
        document.getElementById('debateFinal').innerHTML = "<strong>Final Synthesis:</strong> " + finalAnswer;
      });
    </script>
  </body>
  </html>
  `);
});

// ---------- Math Page ----------
app.get('/math', (req, res) => {
  res.send(`
  <!DOCTYPE html>
  <html>
  <head>
    <title>Math Question</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
      .section { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }
      .round-section { background: #f9f9f9; padding: 10px; margin: 10px 0; }
      .round-title { font-weight: bold; }
      .final-answer { background: #e1ffe1; padding: 10px; margin-top: 20px; border: 1px solid #bbb; }
    </style>
  </head>
  <body>
    <div class="container">
      <nav class="mt-3">
        <a href="/">Home</a> | <a href="/legal">Legal</a> | <a href="/math">Math</a>
      </nav>
      <h1 class="mt-4">Math Question</h1>
      <div class="row">
        <!-- One-Shot Section -->
        <div class="col-md-6 section">
          <h3>One-Shot Approach</h3>
          <p><strong>Question:</strong> ${mathQuery}</p>
          <button id="oneShotBtnMath" class="btn btn-primary">Get Zero-Shot Answer</button>
          <div id="oneShotResultMath" class="mt-3"></div>
        </div>
        <!-- Debate Section -->
        <div class="col-md-6 section">
          <h3>Debate Approach</h3>
          <p><strong>Question:</strong> ${mathQuery}</p>
          <div class="form-group">
            <label for="roundsInputMath">Number of Rounds:</label>
            <input type="number" id="roundsInputMath" class="form-control" value="1" min="1">
          </div>
          <button id="debateBtnMath" class="btn btn-secondary">Start Debate</button>
          <div id="debateRoundsMath" class="mt-3"></div>
          <div id="debateFinalMath" class="final-answer"></div>
        </div>
      </div>
    </div>

    <script>
      document.getElementById('oneShotBtnMath').addEventListener('click', async () => {
        document.getElementById('oneShotResultMath').innerText = "Loading...";
        const response = await fetch('/api/math/one-shot', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        document.getElementById('oneShotResultMath').innerText = data.answer;
      });

      document.getElementById('debateBtnMath').addEventListener('click', async () => {
        const rounds = document.getElementById('roundsInputMath').value;
        document.getElementById('debateRoundsMath').innerHTML = "Loading...";
        document.getElementById('debateFinalMath').innerHTML = "";

        const response = await fetch('/api/math/debate', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rounds: rounds })
        });
        const data = await response.json();

        // Clear the placeholder
        document.getElementById('debateRoundsMath').innerHTML = "";
        
        // Display each round’s data
        data.roundData.forEach(round => {
          const roundDiv = document.createElement('div');
          roundDiv.classList.add('round-section');
          roundDiv.innerHTML = \`
            <div class="round-title">Round \${round.roundNumber}</div>
            <p><strong>Agent 1:</strong> \${round.agent1Answer}</p>
            <p><strong>Agent 2:</strong> \${round.agent2Answer}</p>
            <p><strong>Moderator:</strong> \${round.moderatorAnswer}</p>
          \`;
          document.getElementById('debateRoundsMath').appendChild(roundDiv);
        });

        // Show final synthesis at the bottom
        const finalAnswer = data.finalAnswer || "No final answer returned.";
        document.getElementById('debateFinalMath').innerHTML = "<strong>Final Synthesis:</strong> " + finalAnswer;
      });
    </script>
  </body>
  </html>
  `);
});

// ========== API Endpoints ==========

// ---- Legal Endpoints ----
app.post('/api/legal/one-shot', async (req, res) => {
  try {
    const answer = await getZeroShotResponse(legalQuery);
    res.json({ answer });
  } catch (error) {
    console.error("API Error:", error);
    res.status(500).json({ answer: "Error processing request." });
  }
});

app.post('/api/legal/debate', async (req, res) => {
  const rounds = req.body.rounds ? parseInt(req.body.rounds) : 1;
  try {
    const result = await multiagentDebate(legalQuery, rounds);
    res.json(result); // { roundData: [...], finalAnswer: "..." }
  } catch (error) {
    console.error("API Error:", error);
    res.status(500).json({ finalAnswer: "Error processing request." });
  }
});

// ---- Math Endpoints ----
app.post('/api/math/one-shot', async (req, res) => {
  try {
    const answer = await getZeroShotResponse(mathQuery);
    res.json({ answer });
  } catch (error) {
    console.error("API Error:", error);
    res.status(500).json({ answer: "Error processing request." });
  }
});

app.post('/api/math/debate', async (req, res) => {
  const rounds = req.body.rounds ? parseInt(req.body.rounds) : 1;
  try {
    const result = await multiagentDebate(mathQuery, rounds);
    res.json(result); // { roundData: [...], finalAnswer: "..." }
  } catch (error) {
    console.error("API Error:", error);
    res.status(500).json({ finalAnswer: "Error processing request." });
  }
});

// ========== Start Server ==========
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
