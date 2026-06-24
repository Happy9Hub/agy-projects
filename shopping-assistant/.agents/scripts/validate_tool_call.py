#!/usr/bin/env python3
import sys
import json
import re

def main():
    try:
        # Read from stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            # If no input is received, allow the execution to proceed
            sys.exit(0)

        data = json.loads(input_data)

        tool_name = data.get("tool_name")
        tool_input = data.get("tool_input", {})

        # Extract the command string from tool input
        command = ""
        if isinstance(tool_input, dict):
            command = tool_input.get("CommandLine") or tool_input.get("command") or ""

        # Intercept run_command or Bash tool executions
        if tool_name in ("run_command", "Bash"):
            # Patterns that represent destructive actions
            blocked_patterns = [
                r"rm\s+-rf\s+/",            # rm -rf /
                r"rm\s+-rf\s+\*",           # rm -rf *
                r"rm\s+-rf\s+\.",           # rm -rf .
                r"rm\s+-rf\s+.*?\s+/",      # rm -rf targeting root with intermediate paths
            ]

            for pattern in blocked_patterns:
                if re.search(pattern, command):
                    error_message = f"Access Denied: The command '{command}' was blocked because it matches a destructive pattern."
                    sys.stderr.write(error_message + "\n")

                    # Return structured JSON block decision on stdout
                    print(json.dumps({
                        "decision": "block",
                        "reason": error_message
                    }))
                    sys.exit(2)

    except Exception as e:
        sys.stderr.write(f"Validation hook error: {str(e)}\n")
        sys.exit(0)

    # Allow the tool execution to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()
