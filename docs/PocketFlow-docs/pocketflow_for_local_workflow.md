> https://chatgpt.com/g/g-677464af36588191b9eba4901946557b-pocket-flow-assistant/c/682de4b2-5528-8009-85c2-c2b179b2236d

# Me

Can pocketflow be used as a local automation/flow engine even without an LLM?

# Pocket Flow Assistant

**Yes — Pocket Flow can absolutely be used as a local automation/flow engine without an LLM.**
It’s designed with LLMs in mind but is fundamentally a general-purpose **graph-based workflow engine**.

---

## ✅ Why It Works Without LLMs

Pocket Flow operates around:

- **Nodes**: Modular steps (`prep → exec → post`) — no LLM required.
- **Shared Store**: Central data exchange between nodes.
- **Flows**: Graphs of nodes with flexible branching and looping.

None of this **requires an LLM**. You can replace `call_llm(...)` with:

- file operations
- API calls
- database queries
- system commands
- data transforms

> Think of Pocket Flow as a lightweight Airflow / Prefect / Dagster — but with a 100-line core and simpler design.

---

## 🧠 Common Non-LLM Use Cases

Here are automation examples that Pocket Flow can handle **without any LLM**:

| Task Category       | Examples                                    |
| ------------------- | ------------------------------------------- |
| **File management** | Move/copy/create/delete files, sync folders |
| **ETL**             | Read CSV → transform → write to DB          |
| **Monitoring**      | Poll servers, parse logs, trigger alerts    |
| **Web scraping**    | Fetch pages, extract data, store to DB      |
| **APIs**            | Call APIs → merge data → write results      |
| **Local agents**    | Build tools that react to filesystem/events |

---

## 🔧 Example: Folder Watcher Flow

```python
class CheckFiles(Node):
    def prep(self, shared):
        return os.listdir(shared["watch_path"])

    def exec(self, files):
        return [f for f in files if f.endswith(".txt")]

    def post(self, shared, prep_res, exec_res):
        shared["new_txt_files"] = exec_res
        return "default"
```

That’s a fully functional node — zero LLM involved.

---

## 💡 Summary

| Feature               | Without LLM? | Notes                                     |
| --------------------- | ------------ | ----------------------------------------- |
| Flow design           | ✅           | Fully usable for automation               |
| Node logic            | ✅           | Just write any Python function            |
| Shared store          | ✅           | Works like a global context/dictionary    |
| Async / Batch / Retry | ✅           | Built-in support                          |
| LLM agents            | ❌ optional  | Only needed for language-driven reasoning |

---

Let me know if you want an example project that’s 100% non-LLM — like a file cleanup or ETL automation.
