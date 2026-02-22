from typing import List, Optional, Dict, Any
import msgspec
from .base import BaseTool

# --- Schemas ---

class SequentialThinkingArgs(msgspec.Struct):
    thought: str
    thought_number: int
    total_thoughts: int
    next_thought_needed: bool
    is_revision: Optional[bool] = None
    revises_thought: Optional[int] = None
    branch_from_thought: Optional[int] = None
    branch_id: Optional[str] = None
    needs_more_thoughts: Optional[bool] = None

# --- Tools ---

class SequentialThinkingTool(BaseTool[SequentialThinkingArgs]):
    name = "sequential_thinking"
    description = "A meta-cognitive tool for complex problem solving. Allows breaking down problems into thoughts, revising them, and branching."
    args_schema = SequentialThinkingArgs

    async def run(self, args: SequentialThinkingArgs) -> str:
        # In a real agent, this might persist state to visualizers or logs.
        # For this CLI agent, we echo the thought structure back to the LLM 
        # so it remains in the context window and 'forces' the model to process it.
        
        output = [
            f"THOUGHT {args.thought_number}/{args.total_thoughts}",
            f"Content: {args.thought}"
        ]
        
        if args.is_revision:
            output.append(f"(Revision of thought {args.revises_thought})")
        
        if args.branch_from_thought:
            output.append(f"(Branch from thought {args.branch_from_thought}, ID: {args.branch_id})")
            
        if args.next_thought_needed:
            output.append("Status: Thinking process continues...")
        else:
            output.append("Status: Thinking process complete.")
            
        return "\n".join(output)
