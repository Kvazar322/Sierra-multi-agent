# Sierra - multi-agent-tg-bot

A multi-agent Telegram bot engineered to eliminate Large Language Model (LLM) hallucinations. Sierra uses a hybrid parallel-sequential multi-agent pipeline combining Google Gemini 3.6 Flash, DeepSeek-v4-Flash, Tencent HY3, and Gemma 4 to debate, cross-verify, and vote on output accuracy.

## Architectural Workflow

* **Sequential Chain (Module 1):** Gemini 3.6 generates an initial answer. Tencent HY3 critiques it, and DeepSeek-v4-Flash synthesizes the response. Gemma 4 acts as an arbiter to calculate model consensus
* **Parallel Consensus (Module 2):** Queries Gemini, DeepSeek, and HY3 simultaneously via asyncio.gather. Gemma 4 tallies vote counts and flags discrepancies.
* **Iterative Refinement (Module 3):** Combines the outputs of Modules 1 & 2. If Iteration Mode is active, Sierra extracts disputed questions and re-runs the resolution loop up to 3 times to isolate facts.

## Hallucination Benchmark

Evaluated on a custom benchmark dataset of 50 complex test questions designed to trigger model hallucinations.

| Model / System | Question Coverage | Ground Truth Accuracy (Covered) | Precision | Top-1 Error Rate |
| :--- | :---: | :---: | :---: | :---: |
| **Sierra 0.5.2** | **76%** | **100%** | **0%** | **10%** |
| Sierra 0.3.0 | 39% | 100% | 0% | 45% |
| Gemini | 100% | 74% | 26% | 26% |
| GPT-4o | 100% | 66% | 34% | 34% |

Top-1 Error Rate measures the error rate when selecting the model's highest-probability answer without applying Sierra's filtering.

## Core Features

* **Multi-Pass Iteration Mode:** Forces Sierra into a 3-loop extraction cycle to resolve discrepancies between agents.
  * **Trade-offs:** Expands context accuracy, but increases token consumption by ~3x and increases overall latency.

* **Token Limit Bypass Mode:** Toggles between a strict 6,000 token limit safety cap and unlimited model output generation.
  * **Warning:** Use at your own risk. Disabling limits can result in extreme token consumption.

* **Detailed vs. Concise Response Strategy(Beta):** Dynamically instructs models to switch between brief summaries and deep-dive technical explanations.

* **Interactive Control Panel:** Manage runtime flags (Iterations, Token Limits, Detailed Answers) directly via Telegram inline keyboards.

* **OСR(Beta):** Allows you to recognize text directly from photos.
  * **Warning:** When using the photo, do not write anything alongside it.

## Setup & Installation

### Option 1: Running from Source

1. Clone the repository:
```
git clone https://github.com/Kvazar322/Sierra-multi-agent.git
cd Sierra-multi-agent
pip install pyTelegramBotAPI google-genai openrouter
```

2. Rename config.json.example to config.json and fill in your credentials.

3. Run the script:
```
python Sierra.py
```

### Option 2: Running Executable (.exe)

1. Go to the **Releases** section on GitHub.
2. Download `Sierra.exe` and `config.json`.
3. Place both files in the same folder.
4. Fill in your credentials in `config.json`.
5. Launch `Sierra.exe`.

## Configuration Keys

* **`openrouter`**: OpenRouter API key (obtained from [OpenRouter](https://openrouter.ai/)).
* **`api_gemini`**: Google Gemini API key (obtained from [Google AI Studio](https://aistudio.google.com/)).
* **`id_chat`**: Target User ID where status notifications and error logs will be sent.
* **`tg_api`**: Telegram Bot Token (obtained from [@BotFather](https://t.me/BotFather)).
