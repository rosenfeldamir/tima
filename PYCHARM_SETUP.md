# PyCharm Setup Guide for Tima

## 1. Configure Python Interpreter

1. Open **File → Settings → Project: tima → Python Interpreter**
2. Click the gear icon ⚙️ → **Add Interpreter → Add Local Interpreter**
3. Select **Existing environment**
4. Browse to: `C:\code\tima\.venv\Scripts\python.exe`
5. Click **OK**

## 2. Run Configuration

### Option A: Using UV (Recommended)

1. **Run → Edit Configurations...**
2. Click **+** → **Shell Script**
3. Configure:
   - **Name:** `Tima (uv)`
   - **Script text:** `uv run tima`
   - **Working directory:** `C:\code\tima`
4. Click **OK**

### Option B: Python Module

1. **Run → Edit Configurations...**
2. Click **+** → **Python**
3. Configure:
   - **Name:** `Tima`
   - **Module name:** `tima_timer`  (NOT script path!)
   - **Working directory:** `C:\code\tima`
   - **Python interpreter:** Select the `.venv` interpreter
4. Click **OK**

### Option C: Entry Point Script

1. **Run → Edit Configurations...**
2. Click **+** → **Python**
3. Configure:
   - **Name:** `Tima (script)`
   - **Script path:** `C:\code\tima\.venv\Scripts\tima.exe`
   - **Working directory:** `C:\code\tima`
4. Click **OK**

## 3. Important Paths

- **Project Root:** `C:\code\tima`
- **Virtual Environment:** `C:\code\tima\.venv`
- **Python Executable:** `C:\code\tima\.venv\Scripts\python.exe`
- **Source Code:** `C:\code\tima\src\tima_timer`

## 4. Running the App

After configuration, just click the **Run** button (▶️) or press **Shift+F10**

## 5. Debugging

To debug:
1. Set breakpoints in the code
2. Click the **Debug** button (🐞) or press **Shift+F9**

## 6. Terminal Usage

In PyCharm's terminal, you can run:
```bash
# Install dependencies
uv sync

# Run the app
uv run tima

# Or activate venv first
.venv\Scripts\activate
tima
```

## Common Issues

### Import Errors
- Make sure **Working Directory** is set to `C:\code\tima` (project root)
- Ensure you're using the `.venv` interpreter

### Module Not Found
- Run `uv sync` to install all dependencies
- Verify the interpreter is set to `.venv\Scripts\python.exe`

### Flet Not Found
- The dependency should be `flet[all]>=0.24.0` in `pyproject.toml`
- Run `uv sync --reinstall` if needed
