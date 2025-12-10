# **Mini Agent Workflow Engine**

A lightweight backend workflow engine inspired by LangGraph concepts.
This system supports **nodes**, **state propagation**, **branching**, **looping**, a **tool registry**, and **FastAPI execution APIs**.

No machine learning or frontend is required — everything is rule-based and backend-only.

---

## 🚀 Features

### **Workflow Engine**

* Nodes represent steps in a workflow
* Each node has a **tool** (Python function)
* Shared **state dictionary** flows between nodes
* **Edges** define transitions between nodes
* **Branching** based on state values
* **Looping** supported until a condition is met (e.g., quality threshold)
* Step-wise execution logs

### **Tool Registry**

* Register Python functions as “tools”
* Each tool reads/updates shared state
* Supports sync or async execution

### **FastAPI Endpoints**

| Endpoint                    | Purpose                         |
| --------------------------- | ------------------------------- |
| `POST /graph/create`        | Create a workflow graph         |
| `POST /graph/run`           | Run workflow with initial state |
| `GET /graph/state/{run_id}` | Inspect state/logs of a run     |

---

## ⭐ Included Example Workflow

### **Summarization + Refinement Pipeline**

Steps:

1. Split long text into chunks
2. Summarize chunks
3. Merge all summaries
4. Iteratively refine merged summary until it is short enough
5. Loop stops when word length target is satisfied

---

# 🧱 Project Structure

```
app/
│── main.py          # FastAPI app and API endpoints
│── engine.py        # Core workflow engine
│── tools.py         # Registered tools for example workflow
requirements.txt
README.md
```

---

## ⚙️ Installation & Setup

### **1️⃣ Clone the repo**

```bash
git clone <your_repo_url>
cd <repo_folder>
```

### **2️⃣ Install dependencies**

```bash
pip install -r requirements.txt
```

### **3️⃣ Run FastAPI app**

```bash
uvicorn app.main:app --reload
```

---

## 🌐 Access API (Swagger UI)

After running the server, go to:

👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

⭐ The root URL automatically redirects to `/docs`.

---

## ▶️ Run Example Workflow

Use this example payload inside Swagger for:

### `POST /graph/run`

```json
{
  "graph_id": "<EXAMPLE_GRAPH_ID>",
  "initial_state": {
    "text": "Your long text to be summarized...",
    "chunk_size": 30,
    "target_length": 40,
    "max_iterations": 5
  }
}
```

Output includes:

* `run_id`
* `final_state` (final refined summary)
* `status`
* `log` (each step with timestamp & state snapshot)

Then call:

### `GET /graph/state/{run_id}`

to inspect full state/log.

---

# 🧠 How Workflow Execution Works

A graph is defined using:

* `start_node`
* List of nodes with:

  * `name`
  * `tool`
  * `next` OR
  * `condition_key + next_if_true + next_if_false`

### Execution engine:

1. Starts at `start_node`
2. Executes tool function
3. Updates shared state
4. Logs step
5. Decides next node:

   * direct `next` OR
   * conditional branching
6. Supports looping when condition is false

### Execution stops when:

* `next_node = None`, or
* max iteration limit reached, or
* error

---

# 🛠 Example Tools Implemented

* `split_text`
* `summarize_chunks`
* `merge_summaries`
* `refine_summary` (looping until short enough)

All tools are pure Python — **no ML**.

---

# 📋 Example State Flow

```
text → chunks → summaries → merged_summary
      ↓ loop (refine)
final_summary (under target length)
```

Loop continues until:

```python
state["summary_within_limit"] == True
```
---

## 🙌 Author

**Uppalapati Venkata Ashok Adithya**
AI/ML Engineering Enthusiast
B.Tech CSE – AI/ML
