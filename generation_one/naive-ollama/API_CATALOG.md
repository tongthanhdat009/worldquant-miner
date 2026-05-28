# WorldQuant Brain API Catalog

## Overview

This document catalogs all APIs used in the WorldQuant Miner project, organized by user type.

## Table of Contents

- [Consultant APIs (AI-Powered)](#consultant-apis-ai-powered)
- [User APIs (Dashboard)](#user-apis-dashboard)
- [External APIs](#external-apis)

---

## Consultant APIs (AI-Powered)

These APIs are used by AI consultants (Ollama-powered alpha generators) to interact with WorldQuant Brain.

### Authentication API

| Property | Value |
|----------|-------|
| **Endpoint** | `POST https://api.worldquantbrain.com/authentication` |
| **Purpose** | Authenticate with WorldQuant credentials |
| **Method** | POST |
| **Auth** | Basic Auth (username, password) |

```python
session = requests.Session()
session.auth = (credentials[0], credentials[1])
response = session.post('https://api.worldquantbrain.com/authentication')
```

### Alphas API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/users/self/alphas` |
| **Purpose** | List all alphas in current account |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

Query params:
- `limit=100&offset=0` - pagination
- `status=UNSUBMITTED%1FIS_FAIL` - filter status
- `dateCreated%3E=2025-MM-DD` - start date
- `is.fitness%3E0.5` - min fitness
- `is.sharpe%3E1.0` - min sharpe
- `settings.region=USA` - region filter
- `order=-is.sharpe` - sort descending

```python
url = "https://api.worldquantbrain.com/users/self/alphas?limit=100&offset=0&order=-is.sharpe"
alpha_resp = self.session.get(url)
```

### Simulations API

| Property | Value |
|----------|-------|
| **Endpoint** | `POST https://api.worldquantbrain.com/simulations` |
| **Purpose** | Run alpha simulation/backtest |
| **Method** | POST |
| **Auth** | Basic Auth (session) |

```python
simulation_response = self.session.post('https://api.worldquantbrain.com/simulations', json=sim_data)
# Returns: 201 + Location header for progress polling
```

### Single Alpha API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/alphas/{alpha_id}` |
| **Purpose** | Get single alpha details |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

```python
alpha = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id)
```

### Alpha Submit API

| Property | Value |
|----------|-------|
| **Endpoint** | `POST https://api.worldquantbrain.com/alphas/{alpha_id}/submit` |
| **Purpose** | Submit alpha to WorldQuant |
| **Method** | POST |
| **Auth** | Basic Auth (session) |

```python
url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/submit"
response = self.sess.post(url)
```

### Alpha Check API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/alphas/{alpha_id}/check` |
| **Purpose** | Check alpha validity |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

```python
result = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id + "/check")
```

### Operators API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/operators` |
| **Purpose** | List all available Alpha operators |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

```python
response = self.sess.get('https://api.worldquantbrain.com/operators')
```

### Data Fields API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/data-fields` |
| **Purpose** | List all available data fields |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

Query params:
- `type=REG` - filter by type (e.g., REG, DERIVED, MATRIX)

```python
response = self.sess.get('https://api.worldquantbrain.com/data-fields', params={'type': 'REG'})
```

### Single Alpha API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/alphas/{alpha_id}` |
| **Purpose** | Get single alpha details |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

```python
alpha = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id)
```

### Alpha Submit API

| Property | Value |
|----------|-------|
| **Endpoint** | `POST https://api.worldquantbrain.com/alphas/{alpha_id}/submit` |
| **Purpose** | Submit alpha to WorldQuant |
| **Method** | POST |
| **Auth** | Basic Auth (session) |

```python
url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/submit"
response = self.sess.post(url)
```

### Alpha Check API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/alphas/{alpha_id}/check` |
| **Purpose** | Check alpha validity |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

```python
result = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id + "/check")
```

### Operators API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/operators` |
| **Purpose** | List all available Alpha operators |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

```python
response = self.sess.get('https://api.worldquantbrain.com/operators')
```

### Data Fields API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api.worldquantbrain.com/data-fields` |
| **Purpose** | List all available data fields |
| **Method** | GET |
| **Auth** | Basic Auth (session) |

Query params:
- `type=REG` - filter by type (e.g., REG, DERIVED, MATRIX)

```python
response = self.sess.get('https://api.worldquantbrain.com/data-fields', params={'type': 'REG'})
```

### Settings API

| Property | Value |
|----------|-------|
| **Endpoint** | `GET/PUT https://api.worldquantbrain.com/settings` |
| **Purpose** | Get/Update user settings |
| **Method** | GET/PUT |

---

## User APIs (Dashboard)

These APIs are exposed via the Flask web dashboard for user interaction.

### Status Endpoint

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/status` |
| **Purpose** | Get overall system status (GPU, Ollama, Orchestrator, WorldQuant) |
| **Method** | GET |
| **Returns** | JSON with gpu, ollama, orchestrator, worldquant, recent_activity, statistics |

```python
@app.route('/api/status')
def api_status():
    return jsonify(dashboard.get_system_status())
```

### Logs Endpoint

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/logs` |
| **Purpose** | Get recent system logs |
| **Method** | GET |
| **Query Params** | `lines` (default: 50) |

```python
@app.route('/api/logs')
def api_logs():
    lines = request.args.get('lines', 50, type=int)
    return jsonify({"logs": dashboard.get_logs(lines)})
```

### Alpha Logs Endpoint

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/alpha_logs` |
| **Purpose** | Get alpha generator specific logs |
| **Method** | GET |
| **Query Params** | `lines` (default: 50) |

```python
@app.route('/api/alpha_logs')
def api_alpha_logs():
    lines = request.args.get('lines', 50, type=int)
    return jsonify({"logs": dashboard.get_alpha_generator_logs(lines)})
```

### Trigger Mining Endpoint

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/trigger_mining` |
| **Purpose** | Manually trigger alpha expression mining |
| **Method** | POST |

```python
@app.route('/api/trigger_mining', methods=['POST'])
def api_trigger_mining():
    result = dashboard.trigger_mining()
    return jsonify(result)
```

### Trigger Submission Endpoint

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/trigger_submission` |
| **Purpose** | Manually trigger alpha submission to WorldQuant |
| **Method** | POST |

```python
@app.route('/api/trigger_submission', methods=['POST'])
def api_trigger_submission():
    result = dashboard.trigger_submission()
    return jsonify(result)
```

### Trigger Alpha Generation Endpoint

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/trigger_alpha_generation` |
| **Purpose** | Manually trigger AI alpha generation |
| **Method** | POST |

```python
@app.route('/api/trigger_alpha_generation', methods=['POST'])
def api_trigger_alpha_generation():
    result = dashboard.trigger_alpha_generation()
    return jsonify(result)
```

### Refresh Endpoint

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/refresh` |
| **Purpose** | Refresh system status |
| **Method** | GET |

```python
@app.route('/api/refresh')
def api_refresh():
    return jsonify(dashboard.get_system_status())
```

### Dashboard Web UI

| Property | Value |
|----------|-------|
| **Endpoint** | `/` |
| **Purpose** | Main dashboard HTML page |
| **Method** | GET |

```python
@app.route('/')
def index():
    return render_template('dashboard.html')
```

---

## External APIs

### Ollama API

| Property | Value |
|----------|-------|
| **Endpoint** | `http://localhost:11434` |
| **Purpose** | Local LLM inference API for AI alpha generation |
| **Methods** | GET/POST |

#### List Models

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/tags` |
| **Purpose** | List available Ollama models |

```bash
curl http://localhost:11434/api/tags
```

#### Generate

| Property | Value |
|----------|-------|
| **Endpoint** | `/api/generate` |
| **Purpose** | Generate text with Ollama model |

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Generate alpha idea...",
  "stream": false
}'
```

---

## API Summary by User Type

| User Type | APIs |
|-----------|------|
| **Consultant (AI)** | `/authentication`, `/alphas`, `/alphas/{id}`, `/alphas/{id}/submit`, `/alphas/{id}/check`, `/simulations`, `/operators`, `/data-fields`, `/settings` |
| **User (Dashboard)** | `/`, `/api/status`, `/api/logs`, `/api/alpha_logs`, `/api/trigger_mining`, `/api/trigger_submission`, `/api/trigger_alpha_generation`, `/api/refresh` |
| **External (Ollama)** | `/api/tags`, `/api/generate` |

---

## Notes

- All Consultant APIs require authentication via `credential.txt` (Basic Auth)
- Dashboard APIs are for UI interaction and manual triggering
- Ollama runs locally at `http://localhost:11434`
- Dashboard runs at `http://localhost:5000`