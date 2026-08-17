# Agent Control Plane

[![Agent Control Plane CI](https://github.com/mariajohansen-ai/agent-control-plane/actions/workflows/ci.yml/badge.svg)](https://github.com/mariajohansen-ai/agent-control-plane/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-reference%20architecture-informational)

**Governance infrastructure for multi-agent AI systems.**

Agent Control Plane is a Python reference architecture for supervising multiple specialist AI agents from one policy-aware control layer. It separates agent execution from governance so that routing, permissions, retries, human approval and auditability remain under central control.

> Agents decide **how** to perform bounded work. The control plane decides **whether, when, where and under which policy** they may act.

## Why this matters

As organisations move from individual copilots to networks of autonomous agents, the difficult problem is no longer simply generating an answer. It is controlling what each agent is allowed to do, deciding which agent should receive a task, handling failures safely and preserving human authority over high-impact actions.

This project explores that control layer directly rather than hiding orchestration inside a chain of prompts.

## Architecture

```text
                            HUMAN APPROVAL
                                  │
                                  ▼
┌──────────────┐          ┌─────────────────────┐
│ User / App   │─────────▶│    CONTROL PLANE    │
└──────────────┘          │                     │
                          │  Capability routing │
                          │  Workload control   │
                          │  Retry policy       │
                          │  Approval gates     │
                          │  Audit trail        │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
             ┌────────────┐   ┌────────────┐   ┌────────────┐
             │ Research   │   │ Analysis   │   │ Review     │
             │ Agent      │   │ Agent      │   │ Agent      │
             └────────────┘   └────────────┘   └────────────┘
                                                       │
                                                       ▼
                                                ┌────────────┐
                                                │ Action     │
                                                │ Agent      │
                                                └─────┬──────┘
                                                      │
                                             Human approval
                                             for high-risk work
```

## Current capabilities

- **Agent registry** — specialist agents declare identity, capabilities, concurrency limits and risk level.
- **Capability-based routing** — tasks are sent only to eligible agents.
- **Workload-aware selection** — routing considers active task load.
- **Retry management** — failures are handled by the supervisor rather than hidden inside individual agents.
- **Human approval gates** — high-risk actions cannot execute until explicit approval is recorded.
- **Audit logging** — routing, execution, retries, approvals, successes and failures are recorded.
- **Remote-agent adapter** — HTTP-based agents can be supervised alongside local deterministic workers.
- **Automated CI** — GitHub Actions runs the test suite on repository changes.

## Executive demo scenario

A leadership team asks:

> **Should our organisation deploy an AI agent for a high-impact business process?**

The control plane can coordinate a bounded workflow:

```text
Executive request
      │
      ▼
Research Agent
      │
      ▼
Analysis Agent
      │
      ▼
Risk / Review Agent
      │
      ▼
Proposed Action
      │
      ▼
Human Approval Gate
      │
      ▼
Approved Action Agent
```

The important feature is not that several agents can communicate. It is that the system maintains a **governance boundary above them**.

## Repository structure

```text
agent-control-plane/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── agent_control_plane/
│       ├── __init__.py
│       ├── agents.py
│       ├── cli.py
│       ├── models.py
│       └── orchestrator.py
├── tests/
│   └── test_orchestrator.py
├── README.md
└── pyproject.toml
```

## Run locally

Requires Python 3.11+.

```bash
python -m pip install -e .
agent-control-plane "Assess an AI transformation proposal"
```

To demonstrate the approval gate for a high-risk action:

```bash
agent-control-plane "Assess an AI transformation proposal" --approve-action
```

## Run the tests

```bash
python -m unittest discover -s tests -v
```

The current tests cover routing, retries, approval requirements and failure when no eligible agent is available.

## What this project is — and is not

This is currently a **governance-first reference architecture**, not a production autonomous-agent platform. The included workers are deliberately deterministic so the control-plane behaviour can be tested reliably. A real model provider can be connected behind the existing agent abstraction without changing the central governance model.

That separation is intentional: production credibility comes from controlling agent behaviour, not merely connecting an LLM API.

## Roadmap

### Governance
- Policy-as-code rules per agent and tool
- Scoped credentials and permissions
- Cost and token budgets
- Timeouts and circuit breakers

### Operations
- Persistent event store
- Agent health scoring
- Observability and traces
- Parallel DAG execution

### Model integration
- Provider abstraction for real LLM agents
- OpenAI / Azure AI adapter
- Structured tool permissions
- Executive decision-support demonstration

## Design principle

**Autonomy should exist inside explicit operational boundaries.**

The long-term goal of this project is to demonstrate how organisations can scale from individual AI assistants to governed agent systems without giving up traceability, accountability or human control.
