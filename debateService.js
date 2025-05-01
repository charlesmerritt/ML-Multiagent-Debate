// services/DebateService.js
const fetch = (...args) => import('node-fetch').then(({default: f}) => f(...args));

class DebateService {
  #apiKey;
  #apiUrl;
  #model;

  constructor(apiKey, model = 'gpt-3.5-turbo') {
    this.#apiKey = apiKey;
    this.#apiUrl = 'https://api.openai.com/v1/chat/completions';
    this.#model  = model;
  }

  async oneShot(question) {
    const body = {
      model: this.#model,
      messages: [{role: 'user', content: `Question: ${question}\nProvide a clear and concise answer.`}],
      max_tokens: 150,
      temperature: 0.7
    };
    const json = await this.#post(body);
    return json.choices[0].message.content.trim();
  }

  async debate(question, rounds = 1) {
    const roundData = [];
    let current = question, consensus = '';

    for (let i = 0; i < rounds; i++) {
      const [a1, a2] = await Promise.all([
        this.#agentAnswer(current),
        this.#agentAnswer(current)
      ]);

      const mod = await this.#moderate(current, a1, a2);
      consensus = mod;
      current   = mod;

      roundData.push({round: i + 1, agent1: a1, agent2: a2, moderator: mod});
    }
    return {roundData, final: consensus};
  }

  /* ---------- private helpers ---------- */

  async #agentAnswer(q) {
    const body = {
      model: this.#model,
      messages: [{role: 'user', content: `Question: ${q}\nProvide a detailed answer.`}],
      max_tokens: 200,
      temperature: 0.7
    };
    const json = await this.#post(body);
    return json.choices[0].message.content.trim();
  }

  async #moderate(q, a1, a2) {
    const body = {
      model: this.#model,
      messages: [
        {role: 'system', content: 'You are an AI debate moderator. Analyse the two responses and provide a consensus that corrects errors.'},
        {role: 'user',   content: `Agent 1: ${a1}\nAgent 2: ${a2}\n\nProvide a final consensus answer for: ${q}`}
      ],
      max_tokens: 200,
      temperature: 0.7
    };
    const json = await this.#post(body);
    return json.choices[0].message.content.trim();
  }

  async #post(body) {
    const res = await fetch(this.#apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.#apiKey}`
      },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`OpenAI API ${res.status} ${res.statusText}`);
    return res.json();
  }
}

module.exports = DebateService;
