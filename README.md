# Korra — AI Agent System

Korra is a containerized AI agent platform built using LangGraph,
designed to demonstrate real-world AI orchestration, tool integration,
and full-stack system deployment.

The project combines a Python-based agent backend, custom tool execution,
and a Next.js chat interface into a unified Dockerized environment that
supports real-time, tool-augmented conversations.

---

## 🚀 Overview

Korra showcases how modern AI agents can be structured as modular
software systems rather than standalone scripts. The system integrates:

- LangGraph-based agent orchestration
- Custom Python and C tool execution
- Streaming conversational interface
- REST-based backend communication
- Docker Compose deployment

The architecture mirrors production-style AI services where backend
reasoning, tool execution, and frontend interaction operate as
independent but connected components.

---

## 🧠 System Architecture

User (Browser)
↓
Agent Chat UI (Next.js)
↓
LangGraph Backend (Python)
↓
Tools Layer (Python + C)


### Components

**Backend**
- LangGraph agent workflow
- Tool routing and execution
- Streaming responses

**Tools**
- Custom analysis utilities
- Python + compiled C integration

**Frontend**
- Real-time chat UI
- Streaming agent responses
- Environment-based configuration

**Deployment**
- Docker Compose multi-service setup
- Local development and cloud-ready structure

---

## ⚙️ Technologies Used

**Languages**
- Python
- TypeScript / JavaScript
- C

**Frameworks & Libraries**
- LangGraph
- LangChain ecosystem
- Next.js
- React
- FastAPI-style backend patterns

**Infrastructure**
- Docker
- Docker Compose

---

## ▶️ Running Locally

Clone the repository:

```bash
git clone <your-repo-url>
cd korra

docker compose up --build 
Frontend
http://localhost:3000\
Backend
http://localhost:2024
