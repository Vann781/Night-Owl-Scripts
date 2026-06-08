import fetch from 'node-fetch';
import { readFileSync, writeFileSync, existsSync } from 'fs';

// ─── TOOL DEFINITIONS (sent to Google) ────────────────────────
export const toolDefinitions = [
  {
    name: 'web_search',
    description: `Search the web for current information.
      Use this when you need facts, news, or data you don't know.
      Returns a list of results with titles, URLs, and snippets.
      For best results, use specific search queries.`,
    input_schema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The search query. Be specific and concise.'
        }
      },
      required: ['query']
    }
  },
  {
    name: 'calculator',
    description: `Evaluate a mathematical expression and return the result.
      Use this for any arithmetic, percentages, conversions, or formulas.
      Expression must be valid JavaScript math syntax.
      Examples: "120 * 0.18", "(1500 / 12).toFixed(2)", "Math.sqrt(144)"`,
    input_schema: {
      type: 'object',
      properties: {
        expression: {
          type: 'string',
          description: 'Valid JS math expression to evaluate'
        }
      },
      required: ['expression']
    }
  },
  {
    name: 'notepad',
    description: `Read from or write to a persistent text notepad.
      Use this to save important findings mid-task so you don't forget them,
      or to read back previously saved notes.
      Action 'write' appends text. Action 'read' returns all notes.
      Action 'clear' wipes the notepad.`,
    input_schema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['read', 'write', 'clear'],
          description: 'read | write | clear'
        },
        text: {
          type: 'string',
          description: 'Text to write (only for write action)'
        }
      },
      required: ['action']
    }
  }
];

// ─── TOOL IMPLEMENTATIONS (your actual code) ──────────────────

export async function runTool(name, input) {
  switch (name) {
    case 'web_search':  return webSearch(input.query);
    case 'calculator': return calculator(input.expression);
    case 'notepad':    return notepad(input.action, input.text);
    default: throw new Error(`Unknown tool: ${name}`);
  }
}

// Tool 1: Web Search via Tavily API
// Tool 1: Web Search via Tavily API
async function webSearch(query) {
  // 1. Check if API key exists before even trying
  if (!process.env.TAVILY_API_KEY) {
    return "Error: TAVILY_API_KEY is missing from your .env file.";
  }

  try {
    const response = await fetch('https://api.tavily.com/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: process.env.TAVILY_API_KEY,
        query: query,
        max_results: 5,
        include_answer: true
      })
    });

    // 2. Catch actual API errors (like bad keys or rate limits)
    if (!response.ok) {
      const errorText = await response.text();
      return `API Error: Tavily returned status ${response.status} - ${errorText}`;
    }

    const data = await response.json();
    
    // 3. Handle empty results safely
    if (!data.results || data.results.length === 0) {
      return `No results found for "${query}".`;
    }
    
    // 4. Return clean text
    const results = data.results.map((r, i) =>
      `[${i+1}] ${r.title}\n    ${r.content.slice(0, 300)}\n    URL: ${r.url}`
    ).join('\n\n');
    
    return `Search results for "${query}":\n\n${results}`;
    
  } catch (e) {
    // 5. Catch network crashes and return them as strings so the agent doesn't crash
    return `Network error while searching: ${e.message}`;
  }
}

// Tool 2: Calculator
function calculator(expression) {
  try {
    // Safe eval using Function — avoids dangerous globals
    const result = new Function('Math', `return ${expression}`)(Math);
    return `Result: ${expression} = ${result}`;
  } catch (e) {
    return `Error: could not evaluate "${expression}". ${e.message}`;
  }
}

// Tool 3: Notepad
function notepad(action, text) {
  const FILE = './notepad.txt';
  if (action === 'read') {
    if (!existsSync(FILE)) return 'Notepad is empty.';
    return 'Notepad contents:\\n' + readFileSync(FILE, 'utf8');
  }
  if (action === 'write') {
    const entry = `[${new Date().toLocaleTimeString()}] ${text}\\n`;
    writeFileSync(FILE, entry, { flag: 'a' });
    return 'Saved to notepad.';
  }
  if (action === 'clear') {
    writeFileSync(FILE, '');
    return 'Notepad cleared.';
  }
}