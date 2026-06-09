import { GoogleGenerativeAI } from '@google/generative-ai';
import 'dotenv/config';
import { toolDefinitions, runTool } from './tools.js';
import * as readline from 'readline/promises';
import { stdin as input, stdout as output } from 'process';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const SYSTEM_PROMPT = `You are a helpful research assistant with access to tools.
When answering a question:
1. Break it into sub-tasks
2. Usetools to gather facts — never guess at numbers or current events
3. Use the notepad to save important findings as you go
4. Calculate when needed instead of estimating
5. Synthesize everything into a clear, structured final answer

Be thorough. Use multiple tools if needed. Always cite where facts came from.`;

// Convert Claude-style tool definitions → Gemini format
const geminiTools = [{
  functionDeclarations: toolDefinitions.map(t => ({
    name: t.name,
    description: t.description,
    parameters: t.input_schema
  }))
}];

// A simple helper to pause execution
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// A robust wrapper for sending messages with automatic retries
async function sendMessageWithRetry(chat, message, maxRetries = 5) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await chat.sendMessage(message);
    } catch (error) {
      if (error.status === 503 || error.status === 429) {
        const waitTime = attempt * 4000; // 4s, 8s, 12s...
        console.log(`\n⚠️ API busy (Error ${error.status}). Retrying in ${waitTime / 1000}s...`);
        
        if (attempt === maxRetries) throw error;
        await sleep(waitTime); 
      } else {
        throw error; 
      }
    }
  }
}

async function runAgent(userQuestion) {
  console.log('\n🤖 Agent starting...');
  console.log(`❓ Task: ${userQuestion}\n`);

  const model = genAI.getGenerativeModel({
    model: 'gemini-3.1-flash-lite',
    tools: geminiTools,
    systemInstruction: SYSTEM_PROMPT
  });

  const chat = model.startChat({ history: [] });

  let iteration = 0;
  const MAX_ITERATIONS = 10;
  let currentMessage = userQuestion;

  while (iteration < MAX_ITERATIONS) {
    iteration++;
    console.log(`── Iteration ${iteration} ──────────────────`);

    const result = await sendMessageWithRetry(chat, currentMessage);
    const response = result.response;
    const functionCalls = response.functionCalls();

    if (!functionCalls || functionCalls.length === 0) {
      const finalText = response.text();
      console.log('\n✅ FINAL ANSWER:\n');
      console.log(finalText);
      return finalText;
    }

    console.log(`Stop reason: tool_use (${functionCalls.length} call(s))`);

    const toolResults = [];
    for (const call of functionCalls) {
      console.log(`🔧 Calling: ${call.name}(${JSON.stringify(call.args)})`);

      let toolResult;
      try {
        toolResult = await runTool(call.name, call.args);
      } catch (e) {
        toolResult = `Error running tool: ${e.message}`;
      }

      console.log(`   ↳ ${String(toolResult).slice(0, 120).replace(/\n/g, ' ')}...`);

      toolResults.push({
        functionResponse: {
          name: call.name,
          response: { result: toolResult }
        }
      });
    }
    currentMessage = toolResults;
  }

  throw new Error('Agent hit max iterations without finishing');
}

// ── INTERACTIVE CLI SETUP ──────────────────────────────────────
const rl = readline.createInterface({ input, output });

async function startInteractiveMode() {
  console.log('================================================');
  console.log('🧠 ReAct Agent Initialized');
  console.log('Type your task/question below, or type "exit" to quit.');
  console.log('================================================');

  while (true) {
    const userInput = await rl.question('\n📝 Enter your prompt:\n> ');
    
    // Check if user wants to exit
    if (userInput.trim().toLowerCase() === 'exit') {
      console.log('Goodbye! 👋');
      break;
    }

    // Skip empty lines
    if (!userInput.trim()) continue;

    try {
      await runAgent(userInput);
    } catch (error) {
      console.error("\n❌ Error during execution:", error.message);
    }
  }
  
  rl.close();
}

// Start the loop
startInteractiveMode();