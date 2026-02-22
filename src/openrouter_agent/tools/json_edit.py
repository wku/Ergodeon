import json
from pathlib import Path
import msgspec
from typing import Any, Optional, Literal
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JSONPathError
from .base import BaseTool

# --- Schemas ---

class JSONEditArgs(msgspec.Struct):
    operation: Literal["view", "set", "add", "remove"]
    file_path: str
    json_path: Optional[str] = None
    value: Optional[Any] = None
    pretty_print: bool = True

# --- Tools ---

class JSONEditTool(BaseTool[JSONEditArgs]):
    name = "json_edit"
    description = "Precise JSON editing using JSONPath. Operations: view, set, add, remove."
    args_schema = JSONEditArgs

    async def run(self, args: JSONEditArgs) -> str:
        try:
            path = Path(args.file_path).resolve()
            if not path.exists():
                return f"Error: File {path} does not exist."
            
            # Load JSON
            try:
                content = path.read_text(encoding='utf-8')
                data = json.loads(content)
            except json.JSONDecodeError as e:
                return f"Error decoding JSON file: {e}"

            # Validate input
            if args.operation != "view" and not args.json_path:
                return "Error: 'json_path' is required for set, add, remove operations."

            if args.operation == "view":
                if args.json_path:
                    try:
                        expr = jsonpath_parse(args.json_path)
                        matches = [match.value for match in expr.find(data)]
                        return json.dumps(matches, indent=2 if args.pretty_print else None)
                    except Exception as e:
                        return f"Error parsing/executing JSONPath: {e}"
                else:
                    return json.dumps(data, indent=2 if args.pretty_print else None)

            # Operations requiring path
            try:
                expr = jsonpath_parse(args.json_path)
            except Exception as e:
                return f"Invalid JSONPath: {e}"

            if args.operation == "set":
                if args.value is None:
                    return "Error: 'value' is required for set operation."
                expr.update(data, args.value) # jsonpath-ng update might be tricky with immutable, but usually modifies in place for dicts
                # Note: jsonpath-ng update modifies in place for dicts/lists usually.

            elif args.operation == "add":
                 if args.value is None:
                    return "Error: 'value' is required for add operation."
                 # jsonpath-ng doesn't support 'add' directly in a simple way for all cases, 
                 # specifically for adding to lists or keys to objects IF the path doesn't exist.
                 # Logic from reference tool was complex. Simplified here:
                 # Find parent, then add.
                 matches = expr.find(data)
                 for match in matches:
                     if isinstance(match.value, list):
                         match.value.append(args.value)
                     elif isinstance(match.value, dict):
                         # If value is a dict, merge it? Or expects key in path?
                         # The reference impl handled this by finding parent. 
                         # For simplicity in this port: only support appending to lists found by path.
                         if isinstance(args.value, dict):
                             match.value.update(args.value)
                         else:
                             return "Error: Can only add dict (merge) to a dict target."
                     else:
                         return f"Error: Cannot add to type {type(match.value)}"

            elif args.operation == "remove":
                # JSONPath remove is not standard.
                # Simplified removal: find matches and delete them from parent.
                # This is hard with just jsonpath-ng find. 
                # Re-implementing full logic is complex. 
                # For this iteration, we will implement a basic version:
                # If path parses to a specific key in a dict or index in a list, remove it.
                # BUT jsonpath-ng 'find' returns the value, not the reference to container easily.
                # We will use a workaround: filter out the matches.
                pass 
                # Actually, proper implementation of remove/add with jsonpath is heavy.
                # Let's fallback to 'set' and 'view' as primary reliable features for now,
                # or implement a simpler version of remove/add if specific path.
                return "Error: 'remove' operation not fully supported in this lightweight version yet. Use 'set' to nullify or read -> modify in python -> write."

            # Save
            path.write_text(json.dumps(data, indent=2 if args.pretty_print else None), encoding='utf-8')
            return f"Operation {args.operation} completed successfully."

        except Exception as e:
            return f"Error executing JSON edit: {e}"
