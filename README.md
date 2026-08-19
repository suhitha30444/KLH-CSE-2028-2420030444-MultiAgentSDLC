# Multi-Agent AI Framework for Automated Software Development

## Team Members
| Name | Roll Number |
|---|---|
| Kapilavai Hamsini | 2420030398 |
| Suhitha Chalasani | 2420030444 |
| Sri Raaga Tangirala | 2420030472 |

## Supervisor
Dr. K. Swanthana 

## Abstract
Traditional software development life cycle (SDLC) execution relies heavily on manual, human-driven effort across requirement gathering, design, coding, testing, and documentation, making it time-consuming and inconsistent. A single monolithic LLM struggles to handle an entire project end-to-end due to the complexity and breadth of knowledge required at each stage. Existing LLM-based systems such as ChatDev, MetaGPT, and AgentCoder largely produce isolated functions rather than complete, multi-file, production-ready projects. This project builds a multi-agent pipeline — orchestrated by LangGraph — in which specialized agents (Requirement Analysis, Planning, Frontend, Backend, Code Review, Testing, Documentation) handle distinct SDLC phases, using Llama 3.x via Groq for fast, low-cost inference and Docker for sandboxed testing, with an automatic retry loop between test failure and code regeneration.

## Setup and Execution Instructions
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set your Groq API key as an environment variable: `GROQ_API_KEY=your_key_here` (never commit this — see `.gitignore`)
4. Run the Flask app: `python app.py`
5. Access the interface at `http://localhost:5000`

## Project Structure
- `/src` — source code for all agents and orchestration logic
- `/docs` — design documents, architecture diagrams, literature survey
- `/data` — sample project requirements used for testing (or data source references)
- `/results` — outputs from pipeline runs, evaluation results
- `/reports` — phase deliverables (Review 1, Review 2, Final report)

## Current Phase Status
Review 1 — in progress
