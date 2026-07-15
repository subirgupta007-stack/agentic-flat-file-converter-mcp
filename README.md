# agentic-flat-file-converter-mcp
Agentic Flat File Conversion
# Installation and Local Development SetupKube-SRE

This section explains how to install and configure the Python environment, MCP SDK, Claude Code integration, and optional Ollama integration for the **agentic-flat-file-converter-mcp** project on Windows.

The instructions use:

* Windows 10 or Windows 11
* PowerShell 7 or Windows PowerShell
* Python 3.12
* Visual Studio Code
* Claude Code
* Model Context Protocol, or MCP
* Ollama, when running Claude Code with a local or Ollama-hosted model

---

## 1. Architecture Overview

The local development architecture is:

```text
Developer
    |
    v
Claude Code
    |
    | Model Context Protocol over stdio
    v
agentic-flat-file-converter-mcp MCP Server
    |
    +-- Kubernetes API
    +-- kubectl
    +-- AWS / EKS APIs
    +-- Helm
    +-- Observability systems
```

Claude Code acts as the MCP client or host.

The Python application in `src/mcp_server.py` acts as the MCP server.

The MCP server exposes controlled tools such as:

```text
health_check
get_current_context
list_kubernetes_contexts
inspect_cluster_health
inspect_failed_pods
analyze_pod_logs
inspect_deployments
```

Claude does not communicate directly with Kubernetes. It calls an approved MCP tool, and the MCP server performs the corresponding controlled operation.

MCP is an open standard for connecting AI applications to external tools, data sources, and workflows. The official Python SDK supports MCP tools, resources, prompts, clients, and transports such as standard input/output and Streamable HTTP.

---

# 2. Important Command-Line Terms

Before beginning the installation, it is useful to understand several terms used throughout the instructions.

## 2.1 What is Python?

Python is the programming language used to build the agentic-flat-file-converter-mcp MCP server.

The Python executable runs:

* Python scripts
* MCP server code
* Kubernetes integrations
* AWS SDK operations
* Project tests
* Package installation commands

Example:

```powershell
python --version
```

This asks the Python executable to display its installed version.

---

## 2.2 What is `pip`?

`pip` is the Python package installer.

It downloads and installs Python libraries required by the project, such as:

```text
mcp
kubernetes
boto3
PyYAML
structlog
tenacity
```

For example:

```powershell
python -m pip install boto3
```

This command asks the selected Python interpreter to run the `pip` module and install the AWS SDK for Python.

Using:

```powershell
python -m pip
```

is safer than running only:

```powershell
pip
```

because `python -m pip` guarantees that packages are installed into the same Python interpreter that executed the command. This is especially important when multiple Python versions or virtual environments exist.

Python’s Windows documentation recommends `python -m pip` when the standalone `pip` command cannot be found or may resolve to the wrong interpreter.

> **Important:** `pip` and “pipe” are two different concepts.

---

## 2.3 What is the PowerShell pipe operator?

The PowerShell pipe operator is:

```text
|
```

A pipe sends the output from the command or expression on its left side to the command on its right side.

Example:

```powershell
Get-ChildItem | Where-Object { $_.Extension -eq ".py" }
```

This works as follows:

```text
Get-ChildItem
    |
    | Sends every file and directory to the next command
    v
Where-Object
    |
    | Keeps only files ending in .py
    v
Filtered output
```

The installation instructions also use a pipe when creating files:

```powershell
@'
mcp[cli]
kubernetes
boto3
'@ | Set-Content .\requirements.txt
```

This command has three parts:

1. `@'` and `'@` define a PowerShell multi-line string called a **here-string**.
2. The pipe `|` passes that string to `Set-Content`.
3. `Set-Content` writes the string into `requirements.txt`.

Therefore, the pipe is not part of Python. It is a PowerShell operator that connects commands.

---

## 2.4 What is the PowerShell call operator?

The PowerShell call operator is:

```text
&
```

It tells PowerShell to execute a command whose path is provided as a string or expression.

Example:

```powershell
& .\.venv\Scripts\python.exe --version
```

Without `&`, PowerShell may treat the executable path as plain text rather than execute it.

The project uses `&` frequently because it explicitly runs the Python interpreter located inside `.venv`.

---

## 2.5 What does `python -m` mean?

The `-m` option tells Python to run an installed Python module as a program.

Example:

```powershell
python -m venv .venv
```

This means:

```text
python              Start Python
-m                  Run a module
venv                Run Python's virtual-environment module
.venv               Create the environment in this directory
```

Another example:

```powershell
python -m pip install boto3
```

This tells Python to run the `pip` module.

Using `-m` helps ensure that the module belongs to the selected Python interpreter.

---

## 2.6 What is a virtual environment?

A virtual environment is an isolated Python installation created specifically for one project.

The agentic-flat-file-converter-mcp virtual environment is stored in:

```text
.venv
```

Its Python executable is:

```text
.venv\Scripts\python.exe
```

Its installed packages are separate from:

* The system Python installation
* Other Python projects
* Other virtual environments

This prevents package conflicts. For example, one project can use one version of the Kubernetes SDK while another project uses a different version.

Python recommends creating a virtual environment for each project. A virtual environment contains an isolated Python interpreter and its own installed packages.

The `.venv` directory must not be committed to Git because it contains machine-specific executables and installed dependencies. It can be recreated from `requirements.txt`.

Add this entry to `.gitignore`:

```gitignore
.venv/
```

---

## 2.7 What is `requirements.txt`?

`requirements.txt` lists the Python packages needed by the project.

Example:

```text
mcp[cli]
kubernetes
boto3
PyYAML
python-dotenv
pydantic-settings
structlog
tenacity
```

A developer can install all listed packages using:

```powershell
python -m pip install -r requirements.txt
```

The `-r` option means:

```text
Read package requirements from this file.
```

This makes setup repeatable for other developers and build pipelines.

---

## 2.8 What is MCP?

MCP stands for **Model Context Protocol**.

MCP provides a standardized way for an AI application such as Claude Code to discover and call external tools.

In this project:

```text
Claude Code = MCP client
agentic-flat-file-converter-mcp = MCP server
Kubernetes diagnostic functions = MCP tools
```

An MCP tool has:

* A unique name
* A description
* An input schema
* A structured result
* A Python function implementing the operation

Example:

```python
@mcp.tool()
def health_check() -> dict:
    return {
        "status": "OK",
        "server": "agentic-flat-file-converter-mcp",
    }
```

The `@mcp.tool()` decorator registers the Python function as a tool that Claude can discover and invoke. MCP tools allow models to interact with external systems, APIs, databases, and computations through defined schemas.

---

## 2.9 What is `stdio`?

`stdio` means **standard input and standard output**.

A local stdio MCP server does not require an HTTP port.

Instead:

1. Claude Code starts the Python MCP process.
2. Claude sends MCP messages to the process through standard input.
3. The Python server sends responses through standard output.
4. Claude stops the process when the Claude session ends.

The communication flow is:

```text
Claude Code
    |
    | standard input
    v
Python MCP Server
    |
    | standard output
    v
Claude Code
```

Stdio is appropriate for local MCP servers that need access to local commands, scripts, kubeconfig, AWS profiles, or other workstation resources. Claude Code documents stdio servers as local processes suited to custom scripts and direct system access.

---

# 3. Prerequisites

Before installing the project, verify that the following are available:

```text
Git
Visual Studio Code
PowerShell
Claude Code
Optional: Ollama
Optional: kubectl
Optional: AWS CLI
Optional: Helm
```

Verify Git:

```powershell
git --version
```

Verify Claude Code:

```powershell
claude --version
```

Verify Ollama, when used:

```powershell
ollama --version
```

Verify kubectl:

```powershell
kubectl version --client
```

Verify AWS CLI:

```powershell
aws --version
```

---

# 4. Open the Project Directory

Open PowerShell and move to the repository root:

```powershell
cd C:\Users\sssgu\source\repo\agentic-flat-file-converter-mcp
```

Verify the location:

```powershell
Get-Location
```

Expected location:

```text
C:\Users\sssgu\source\repo\agentic-flat-file-converter-mcp
```

List the project files:

```powershell
Get-ChildItem
```

All installation commands should be run from the repository root unless otherwise specified.

---

# 5. Verify the Python Installation

Run:

```powershell
python --version
```

A valid response resembles:

```text
Python 3.12.x
```

Check which Python executable PowerShell found:

```powershell
Get-Command python
where.exe python
```

A valid Python installation commonly resembles:

```text
C:\Users\<username>\AppData\Local\Programs\Python\Python312\python.exe
```

## WindowsApps alias problem

When the only result is:

```text
C:\Users\<username>\AppData\Local\Microsoft\WindowsApps\python.exe
```

and `Get-Command` reports version `0.0.0.0`, Windows has found an application execution alias rather than a usable Python runtime.

Install Python 3.12:

```powershell
winget install --exact --id Python.Python.3.12
```

After installation:

1. Close every VS Code window.
2. Close PowerShell.
3. Reopen VS Code.
4. Open a new PowerShell terminal.
5. Run `python --version` again.

Python’s Windows documentation recommends creating project environments with `python -m venv`. It also documents checking Windows application execution aliases when `python` or `py` does not resolve correctly.

---

# 6. Create the Virtual Environment

From the repository root, run:

```powershell
python -m venv .venv
```

This command:

1. Starts the installed Python interpreter.
2. Runs Python’s built-in `venv` module.
3. Creates a directory named `.venv`.
4. Copies or links the Python runtime into the environment.
5. Creates an isolated package installation directory.
6. Installs or makes `pip` available inside the environment.

Verify that the environment was created:

```powershell
Test-Path .\.venv\Scripts\python.exe
```

Expected result:

```text
True
```

Check the virtual-environment Python version:

```powershell
& .\.venv\Scripts\python.exe --version
```

Expected:

```text
Python 3.12.x
```

---

# 7. Activate the Virtual Environment

Activation is optional because every command in this guide can directly call:

```text
.\.venv\Scripts\python.exe
```

To activate the environment in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the prompt usually starts with:

```text
(.venv)
```

Example:

```text
(.venv) PS C:\Users\sssgu\source\repo\agentic-flat-file-converter-mcp>
```

Activation changes the current shell’s PATH so that:

```powershell
python
pip
```

resolve to the executables inside `.venv`.

## PowerShell execution-policy error

When PowerShell reports that `Activate.ps1` cannot be loaded because running scripts is disabled, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

`-Scope Process` changes the policy only for the current PowerShell process. Closing the terminal removes that temporary setting.

Alternatively, do not activate the environment. Run its Python executable directly:

```powershell
& .\.venv\Scripts\python.exe
```

Direct execution is explicit and avoids activation-policy issues.

---

# 8. Upgrade `pip`

Run:

```powershell
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
```

This command:

1. Uses the Python executable inside `.venv`.
2. Runs that interpreter’s `pip` module.
3. Downloads a newer compatible version of `pip`.
4. Updates `pip` only inside this project environment.

Verify:

```powershell
& .\.venv\Scripts\python.exe -m pip --version
```

The returned path should contain:

```text
agentic-flat-file-converter-mcp\.venv
```

This confirms that the project-specific package installer is being used.

---

# 9. Create `requirements.txt`

Skip this step when `requirements.txt` already exists.

Create the initial file with PowerShell:

```powershell
@'
mcp[cli]
kubernetes
boto3
PyYAML
python-dotenv
pydantic-settings
structlog
tenacity
'@ | Set-Content .\requirements.txt
```

What this command does:

```text
@' ... '@
    Creates a literal multi-line PowerShell string.

|
    Pipes the multi-line string to the next command.

Set-Content
    Writes the received content to a file.

.\requirements.txt
    Specifies the destination file.
```

Verify the file:

```powershell
Get-Content .\requirements.txt
```

## Dependency purposes

### `mcp[cli]`

Provides the official Python SDK and CLI support for building MCP servers and clients.

It includes support for:

* MCP tools
* MCP resources
* MCP prompts
* Local stdio servers
* Streamable HTTP servers
* MCP development utilities

### `kubernetes`

Provides the official Kubernetes Python client.

It allows the agent to communicate with the Kubernetes API for operations such as:

* Listing pods
* Reading deployments
* Inspecting events
* Reading logs
* Examining node conditions

### `boto3`

Provides the AWS SDK for Python.

It can be used for:

* EKS cluster discovery
* CloudWatch queries
* IAM identity checks
* Auto Scaling group inspection
* EC2 and VPC metadata
* S3 operations

### `PyYAML`

Parses and generates YAML.

Kubernetes manifests and Helm values commonly use YAML.

The Python import name is:

```python
import yaml
```

even though the package name is `PyYAML`.

### `python-dotenv`

Loads local development configuration from a `.env` file.

Sensitive values must not be committed to Git.

### `pydantic-settings`

Provides validated, typed application configuration.

It can verify that required settings exist and have the correct format before the server starts.

### `structlog`

Provides structured logging.

Instead of unstructured messages, logs can contain searchable fields such as:

```json
{
  "event": "pod_inspection",
  "cluster": "development",
  "namespace": "payments",
  "correlation_id": "abc-123"
}
```

### `tenacity`

Provides retry handling for temporary failures such as:

* Kubernetes API timeouts
* AWS throttling
* Intermittent network errors

Retries should be used only for operations that are safe to repeat.

---

# 10. Install the Dependencies

Run:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

This command:

```text
.\.venv\Scripts\python.exe
    Uses the project-specific Python interpreter.

-m pip
    Runs pip from that interpreter.

install
    Requests package installation.

-r
    Reads package names from a requirements file.

.\requirements.txt
    Identifies the package list.
```

Verify installed packages:

```powershell
& .\.venv\Scripts\python.exe -m pip list
```

---

# 11. Verify the Python Dependencies

Use this one-line verification command:

```powershell
& .\.venv\Scripts\python.exe -c "import boto3, kubernetes, mcp, yaml, structlog, tenacity; print('All agentic-flat-file-converter-mcp dependencies installed successfully')"
```

Expected result:

```text
All agentic-flat-file-converter-mcp dependencies installed successfully
```

The `-c` option tells Python to execute the supplied text as Python code.

For a multi-line verification script, pipe the script into Python:

```powershell
@'
import boto3
import kubernetes
import mcp
import yaml
import structlog
import tenacity

print("All agentic-flat-file-converter-mcp dependencies installed successfully")
'@ | & .\.venv\Scripts\python.exe -
```

The final hyphen:

```text
-
```

tells Python to read source code from standard input.

This is the correct way to combine a PowerShell here-string with Python. Passing a here-string directly to `python -c` can cause PowerShell quoting problems.

---

# 12. Verify or Create the MCP Server

Check whether the MCP server exists:

```powershell
Test-Path .\src\mcp_server.py
```

When the result is:

```text
True
```

do not overwrite the file.

When the result is:

```text
False
```

create the source directory:

```powershell
New-Item -ItemType Directory -Force .\src
```

Create a minimal MCP server:

```powershell
@'
from __future__ import annotations

import shutil
from typing import Any

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("agentic-flat-file-converter-mcp")


@mcp.tool()
def health_check() -> dict[str, Any]:
    """Check whether the agentic-flat-file-converter-mcp MCP server is operational."""
    return {
        "status": "OK",
        "server": "agentic-flat-file-converter-mcp",
        "mode": "read-only",
        "kubectl_available": shutil.which("kubectl") is not None,
        "helm_available": shutil.which("helm") is not None,
        "aws_cli_available": shutil.which("aws") is not None,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
'@ | Set-Content .\src\mcp_server.py
```

The important parts are:

```python
mcp = FastMCP("agentic-flat-file-converter-mcp")
```

This creates the MCP server.

```python
@mcp.tool()
```

This registers the following Python function as an MCP tool.

```python
mcp.run(transport="stdio")
```

This starts the server using standard input/output communication.

FastMCP handles connection management, protocol messages, tool schemas, and routing between the MCP client and Python functions.

---

# 13. Validate the MCP Server Code

Compile the Python source:

```powershell
& .\.venv\Scripts\python.exe -m compileall .\src
```

This checks Python syntax and creates compiled bytecode files.

A successful command must not display:

```text
SyntaxError
```

Test the server import:

```powershell
& .\.venv\Scripts\python.exe -c "from src.mcp_server import mcp; print('Kube-SRE MCP server imported successfully')"
```

Expected:

```text
Kube-SRE MCP server imported successfully
```

Test the health-check function directly:

```powershell
& .\.venv\Scripts\python.exe -c "from src.mcp_server import health_check; print(health_check())"
```

Expected output resembles:

```text
{
    'status': 'OK',
    'server': 'agentic-flat-file-converter-mcp',
    'mode': 'read-only',
    'kubectl_available': True,
    'helm_available': True,
    'aws_cli_available': True
}
```

A value of `False` for an optional command means that command is either not installed or not available through PATH. It does not necessarily mean that the MCP Python server is broken.

---

# 14. Configure Claude Code for the MCP Server

Claude Code must know:

1. The MCP server name
2. The transport type
3. Which Python executable to run
4. Which Python script starts the server

## Project-scoped configuration

The recommended configuration for this repository is project scope.

Project scope creates:

```text
.mcp.json
```

in the repository root.

A project-scoped server can be shared with the repository, but Claude requires each developer to trust and approve it before execution.

Resolve the full paths:

```powershell
$pythonPath = (Resolve-Path .\.venv\Scripts\python.exe).Path
$serverPath = (Resolve-Path .\src\mcp_server.py).Path

Write-Host "Python executable: $pythonPath"
Write-Host "MCP server: $serverPath"
```

Register the MCP server:

```powershell
claude mcp add --transport stdio --scope project agentic-flat-file-converter-mcp -- "$pythonPath" "$serverPath"
```

Command explanation:

```text
claude mcp add
    Adds a new MCP server to Claude Code.

--transport stdio
    Configures Claude to communicate with the server through
    standard input and standard output.

--scope project
    Stores the shared configuration in the repository's .mcp.json.

agentic-flat-file-converter-mcp
    Assigns a unique name to the MCP server.

--
    Separates Claude CLI options from the command that starts the server.

"$pythonPath"
    Specifies the virtual-environment Python executable.

"$serverPath"
    Specifies the Python MCP server script.
```

The double dash is required because everything before it belongs to the Claude CLI, while everything after it is passed to the MCP server command.

---

# 15. Verify the MCP Registration

List configured MCP servers:

```powershell
claude mcp list
```

View this server’s configuration:

```powershell
claude mcp get agentic-flat-file-converter-mcp
```

Possible statuses include:

```text
Connected
Pending approval
Failed to connect
Rejected
```

A newly added project-scoped server may appear as:

```text
Pending approval
```

This is expected until the repository is trusted and the server is approved inside Claude Code.

Verify the generated file:

```powershell
Get-Content .\.mcp.json
```

Do not store the following in `.mcp.json`:

* AWS access keys
* GitHub tokens
* Passwords
* Kubernetes service-account tokens
* Private certificates
* Production credentials

---

# 16. Start Claude Code

Start Claude directly:

```powershell
claude
```

When Claude asks whether the project directory is trusted, approve it only after reviewing the repository and `.mcp.json`.

Inside Claude Code, run:

```text
/mcp
```

Select:

```text
agentic-flat-file-converter-mcp
```

Approve or enable the project MCP server.

Run `/mcp` again and verify that the server is connected.

Claude Code exposes `/mcp` as the interactive command for checking MCP status and approving configured servers.

---

# 17. Test the MCP Server Through Claude

Inside Claude Code, enter:

```text
Use the agentic-flat-file-converter-mcp MCP server's health_check tool.
Show me the complete structured result.
```

Expected result resembles:

```json
{
  "status": "OK",
  "server": "agentic-flat-file-converter-mcp",
  "mode": "read-only",
  "kubectl_available": true,
  "helm_available": true,
  "aws_cli_available": true
}
```

This proves that:

1. Claude discovered the MCP server.
2. Claude launched the Python process.
3. Claude communicated with it over stdio.
4. The MCP server discovered the `health_check` tool.
5. Claude invoked the Python function.
6. The Python server returned a structured result.

---

# 18. Run Claude Code Through Ollama

When Ollama is installed, start Claude Code from the repository root:

```powershell
cd C:\Users\sssgu\source\repo\agentic-flat-file-converter-mcp
ollama launch claude
```

Ollama connects Claude Code to compatible local or cloud models through an Anthropic-compatible API.

Inside Claude Code, verify MCP:

```text
/mcp
```

Then test:

```text
Use the agentic-flat-file-converter-mcp MCP server's health_check tool.
```

For agentic coding tasks, use a model with a sufficiently large context window. Ollama recommends a context window of at least 64K tokens for larger coding repositories.

---

# 19. Reinstall the Project on Another Computer

After cloning the repository:

```powershell
git clone <repository-url>
cd agentic-flat-file-converter-mcp
```

Install Python, then create the environment:

```powershell
python -m venv .venv
```

Install dependencies:

```powershell
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Verify:

```powershell
& .\.venv\Scripts\python.exe -m compileall .\src
& .\.venv\Scripts\python.exe -c "from src.mcp_server import mcp; print('MCP import successful')"
```

Start Claude:

```powershell
claude
```

Approve the repository and project MCP configuration, then run:

```text
/mcp
```

---

# 20. Common Troubleshooting

## `py` is not recognized

Use:

```powershell
python -m venv .venv
```

The `py` launcher is not required when the `python` command works.

---

## `python` points to WindowsApps

Check:

```powershell
Get-Command python
where.exe python
```

Install a real Python runtime and restart the terminal.

---

## `requirements.txt` does not exist

Create it using the command in Step 9.

Verify:

```powershell
Test-Path .\requirements.txt
```

---

## `pip` is not recognized

Use:

```powershell
& .\.venv\Scripts\python.exe -m pip --version
```

Do not rely on the global `pip` command.

---

## PowerShell cannot activate `.venv`

Use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Or avoid activation and call `.venv\Scripts\python.exe` directly.

---

## Python reports a quoting `SyntaxError`

For one-line code, use:

```powershell
& .\.venv\Scripts\python.exe -c "print('Test successful')"
```

For multi-line code, pipe a here-string into Python:

```powershell
@'
print("Test successful")
'@ | & .\.venv\Scripts\python.exe -
```

---

## `/mcp` reports “No MCP servers configured”

Exit Claude and verify from the repository root:

```powershell
Get-Location
Test-Path .\.mcp.json
claude mcp list
claude mcp get agentic-flat-file-converter-mcp
```

Make sure Claude was launched from:

```text
C:\Users\sssgu\source\repo\agentic-flat-file-converter-mcp
```

---

## MCP server is pending approval

Start Claude interactively:

```powershell
claude
```

Accept repository trust and use:

```text
/mcp
```

to approve the server.

---

## MCP server failed to connect

Run:

```powershell
& .\.venv\Scripts\python.exe -m compileall .\src
& .\.venv\Scripts\python.exe -c "import mcp; print('MCP package available')"
& .\.venv\Scripts\python.exe -c "from src.mcp_server import mcp; print('Server import successful')"
```

Then run:

```powershell
claude doctor
claude mcp get agentic-flat-file-converter-mcp
```

---

## `% claude` or `~% ollama` produces an error

Do not type shell prompt symbols copied from documentation.

Incorrect:

```powershell
% claude
~% ollama
```

Correct:

```powershell
claude
ollama
```

In PowerShell, `%` is an alias for `ForEach-Object`; it is not a prompt character that should be included in commands.

---

# 21. Security Recommendations

The initial agentic-flat-file-converter-mcp MCP tools should be read-only.

Recommended initial capabilities:

```text
List resources
Read resource status
Read events
Read logs
Inspect metrics
Analyze configuration
Generate recommendations
```

Avoid enabling these operations until approval controls are implemented:

```text
kubectl delete
kubectl apply
kubectl patch
kubectl scale
kubectl rollout restart
helm upgrade
helm uninstall
AWS infrastructure modifications
```

Future write operations should include:

* Explicit human approval
* Cluster and namespace allowlists
* Production-environment restrictions
* Command validation
* Dry-run support
* Audit logging
* Correlation IDs
* Timeouts
* Least-privilege Kubernetes RBAC
* Least-privilege AWS IAM
* Protection against arbitrary shell execution

---

# 22. Complete Installation Command Summary

From the repository root:

```powershell
cd C:\Users\sssgu\source\repo\agentic-flat-file-converter-mcp

python --version
python -m venv .venv

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt

& .\.venv\Scripts\python.exe -m compileall .\src
& .\.venv\Scripts\python.exe -c "from src.mcp_server import mcp; print('Kube-SRE MCP server imported successfully')"

$pythonPath = (Resolve-Path .\.venv\Scripts\python.exe).Path
$serverPath = (Resolve-Path .\src\mcp_server.py).Path

claude mcp add --transport stdio --scope project agentic-flat-file-converter-mcp -- "$pythonPath" "$serverPath"

claude mcp list
claude mcp get agentic-flat-file-converter-mcp

ollama launch claude
```

Inside Claude Code:

```text
/mcp
```

Then:

```text
Use the agentic-flat-file-converter-mcp MCP server's health_check tool and show the complete result.
```

