# Agent Control Plane

A governance-first orchestration layer for controlling multiple AI agents.

This project demonstrates a supervisor that registers specialist agents, routes work by capability, enforces approval gates for high-risk actions, retries failed work, and records an audit trail.

## Core idea

Agents decide how to perform bounded work. The control plane decides whether, when, where, and under which policy they may act.

## Architecture

User or system -> Control Plane -> Research / Analysis / Review / Action agents

The Control Plane provides:
- capability-based routing
- workload control
- retry policy
- human approval gates
- audit logging

## Run

Requires Python 3.11+.

```bash
python -m pip install -e .
agent-control-plane "Assess an AI transformation proposal"
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- policy-as-code
- persistent event store
- budget and token ceilings
- circuit breakers
- agent health scoring
- parallel DAG execution
- scoped credentials
- observability
- real model/provider adapters
