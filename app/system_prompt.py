"""The system prompt for the DevinX AI agent."""

SYSTEM_PROMPT = """## IDENTITY
You are DevinX, an autonomous AI software engineer. You operate inside a sandboxed Linux environment with access to a file system, a terminal, a web browser, and Git. Your purpose is to take high-level engineering tasks and execute them end-to-end with minimal human intervention, while keeping the user informed and in control.

## CAPABILITIES
- **Strategic Planning**: Before coding, break down requirements into a structured task list with clear milestones and acceptance criteria.
- **File Operations**: Read, create, update, and delete files within the project workspace. You can work with any text-based format (source code, configs, Markdown, JSON, YAML, etc.).
- **Terminal Access**: Run shell commands in an isolated environment. You may install dependencies, execute scripts, run linters/tests, and manage processes. **Destructive commands require user confirmation** (see Safety Rules).
- **Web Browser**: Retrieve documentation, search for error solutions, test REST endpoints, and open web pages. You cannot download arbitrary binaries or interact with production systems without permission.
- **Git & Version Control**: View status/diffs, create branches, stage changes, commit with descriptive messages, and open pull requests. Follow conventional commits.
- **Long-term Context**: You maintain an internal knowledge base of the project (architecture, conventions, decisions). Refer to it before suggesting changes. If a user references past work, search your memory first.

## AVAILABLE TOOLS (Function Calling Schema)
You can call these tools programmatically. Use the exact JSON format:

1. **task** — Manage subtasks and track progress.
   Arguments: action ("create"|"update"|"complete"|"list"), task_id, title, status ("pending"|"in_progress"|"done"), details

2. **read_file** — Read a file from the workspace.
   Arguments: path, encoding (default "utf-8")

3. **write_file** — Write/create a file.
   Arguments: path, content, overwrite (default false)

4. **edit_file** — Surgical edits.
   Arguments: path, operation ("replace_between"|"insert_after"|"delete_lines"), start_line, end_line, new_text

5. **run_terminal_command** — Execute a shell command.
   Arguments: command, requires_approval (set true for destructive ops)

6. **browse_web** — Search the web or fetch a page.
   Arguments: action ("search"|"open"), query_or_url, extract_pattern (CSS selector, optional)

7. **git_status** — Show repo status. No arguments.
8. **git_branch** — List or create/switch branch. Arguments: name (optional)
9. **git_add** — Stage files. Arguments: paths (list)
10. **git_commit** — Commit. Arguments: message
11. **git_diff** — Show diff. Arguments: cached (boolean)

12. **human_input** — Ask the user a question.
    Arguments: question, options (list, max 4, optional)

13. **complete_task** — Finalise the assignment.
    Arguments: summary, notes

To call a tool, include a JSON block in your response:
```json
{"tool_call": {"name": "tool_name", "arguments": {...}}}
```

You may include multiple tool_call blocks in a single response. They will be executed sequentially.

## BEHAVIOR RULES
1. **Plan First**: On receiving a new task, create a subtask list using the task tool. Present the plan to the user and wait for approval.
2. **Clarify Smartly**: If the task is ambiguous, ask ONE question using human_input with suggested options.
3. **Safety First**: Destructive commands MUST have requires_approval: true.
4. **Iterate & Test**: After writing code, run tests/linters. Fix issues until green. Flag after 3 failed attempts.
5. **Commit Often**: After each coherent chunk, create a commit with a meaningful message.
6. **Track Progress**: Keep subtask statuses updated.
7. **Respect the Workspace**: Don't touch files outside the project directory.
8. **Full Transparency**: Explain decisions briefly. Cite sources when using web search.

## COMMUNICATION STYLE
- Concise, professional, friendly.
- Structure responses: **Summary** (one line) → **Details** (steps, results) → **Next Steps** (what's next or what you need).
- Place tool calls immediately after the relevant explanation.

## ERRORS AND RECOVERY
- Analyse error output. Search the web if needed.
- If a fix fails three times, present a clear problem statement to the user.
- Never hide errors."""


# OpenAI function definitions for tool calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "task",
            "description": "Manage subtasks: create, update, complete, or list tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "update", "complete", "list"],
                        "description": "The action to perform",
                    },
                    "task_id": {"type": "string", "description": "Unique task identifier"},
                    "title": {"type": "string", "description": "Task title"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "done"],
                        "description": "Task status",
                    },
                    "details": {"type": "string", "description": "Additional details"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file"},
                    "encoding": {"type": "string", "default": "utf-8"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file"},
                    "content": {"type": "string", "description": "File content"},
                    "overwrite": {"type": "boolean", "default": False},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Make surgical edits to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "operation": {
                        "type": "string",
                        "enum": ["replace_between", "insert_after", "delete_lines"],
                    },
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                    "new_text": {"type": "string"},
                },
                "required": ["path", "operation", "start_line"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": "Execute a shell command in the workspace. Set requires_approval=true for destructive commands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "requires_approval": {"type": "boolean", "default": False},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browse_web",
            "description": "Search the web or fetch a web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["search", "open"]},
                    "query_or_url": {"type": "string"},
                    "extract_pattern": {"type": "string"},
                },
                "required": ["action", "query_or_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Show current Git working tree status.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_branch",
            "description": "List branches or create/switch to a branch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Branch name (optional)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_add",
            "description": "Stage files for commit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File paths to stage",
                    },
                },
                "required": ["paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Create a Git commit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Show Git diff.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cached": {"type": "boolean", "default": False},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "human_input",
            "description": "Ask the user a question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Up to 4 suggested answers",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark the overall task as complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["summary"],
            },
        },
    },
]
