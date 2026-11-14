# AgentGuard 🛡️
![Attack tests](https://github.com/ruchirakarle/agentguard/actions/workflows/tests.yml/badge.svg)

**A secure sandbox and red-team test suite for AI agents.**
AgentGuard lets an LLM agent run code and read files, but every action passes through a policy check, runs inside a locked-down Docker container, and is logged. A suite of attack tests proves the guardrails hold even when the model is tricked.

## How it works

```
User ──▶ Agent (Ollama LLM) ──▶ Guard ──▶ Policy check ──▶ Sandbox (Docker) ──▶ Result
                                   │
                                   └──▶ Logger (SQLite) records every call, allowed or blocked
```

**Security design:** assume the model is compromised. A prompt injection can make the model *ask* for anything, so safety can't depend on the model behaving. It depends on two layers:

1. **Policy layer** (`policy.yaml`): allowed tools, workspace-only file access, blocked code patterns.
2. **Sandbox layer** (`sandbox.py`): no network, read-only filesystem, non-root user, all Linux capabilities dropped, memory / CPU / process / time limits.

The pattern blocklist is intentionally treated as a weak first filter; the container is the real security boundary.

## Results


<img width="1182" height="813" alt="projectagentai" src="https://github.com/user-attachments/assets/2eeab385-30ef-4308-9338-70799f4c9fd5" />


| Attack category | Tests | Blocked by |
|---|---|---|
| Escape the workspace (path traversal, absolute paths) | 3 | Policy |
| Unknown / unauthorized tools | 1 | Policy |
| Shell commands, subprocess, obfuscated imports | 3 | Policy |
| Infinite loop, memory bomb, thread flood, output flood | 4 | Sandbox |
| Internet access, writing files | 2 | Sandbox |

_Fill in your real numbers from `python report.py` here (total calls, blocked, median sandbox time)._

## Run it (Windows, PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull llama3.2
pytest                  # attack tests (needs Docker Desktop running)
python report.py        # summary numbers
python agent.py         # chat with the agent
pytest -m llm -s        # end-to-end prompt-injection test with the real model
```

## Tech
Python · Docker · Ollama · pytest · SQLite · YAML

## Roadmap
- [ ] OpenTelemetry tracing
- [ ] Expose tools via MCP
- [ ] FastAPI dashboard deployed on Azure Container Apps
- [ ] GitHub Actions running the attack suite on every push
- [ ] 50+ attack tests
