# [WFGY] Zone: SAFE | λ: 0.2 | Action: Verify nested loops context isolation bug in orchestrator

import sys
import asyncio
from pathlib import Path

# Add brain directory to python path
sys.path.append(str(Path(__file__).parent / "brain"))

from orchestrator import Orchestrator

async def test_nested_loops():
    # Recipe with nested loops:
    # Outer loop runs over ["A", "B"]
    # Inner loop runs over ["1", "2"]
    # Step inside outer loop (after inner loop) writes a file or prints the outer item
    
    output_log = []
    
    # Custom primitive execution to record logs
    class TestOrchestrator(Orchestrator):
        async def run_recipe(self, recipe_data: dict, *args, **kwargs) -> bool:
            # We intercept execution to log variables
            steps = recipe_data.get("steps", [])
            for s in steps:
                prim = s.get("primitive")
                if prim == "io.write_file":
                    # Record the resolved content
                    resolved_args = self.resolve_secrets(s.get("args", {}))
                    content = resolved_args.get("content")
                    output_log.append(content)
            return await super().run_recipe(recipe_data, *args, **kwargs)

    recipe = {
        "plan_id": "nested_loops_test",
        "intent_analysis": "Test nested loops context isolation",
        "steps": [
            {
                "step": 1,
                "primitive": "core.loop",
                "depends_on": [],
                "args": {
                    "loop_over": "variables",
                    "items_source": "A,B",
                    "steps": [
                        {
                            "step": 10,
                            "primitive": "core.loop",
                            "depends_on": [],
                            "args": {
                                "loop_over": "variables",
                                "items_source": "1,2",
                                "steps": [
                                    {
                                        "step": 100,
                                        "primitive": "io.write_file",
                                        "args": {
                                            "path": "dummy.txt",
                                            "content": "Inner: ${ITER_ITEM}"
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "step": 20,
                            "primitive": "io.write_file",
                            "depends_on": [10],
                            "args": {
                                "path": "dummy.txt",
                                "content": "Outer: ${ITER_ITEM}"
                            }
                        }
                    ]
                }
            }
        ]
    }

    orch = TestOrchestrator()
    success = await orch.run_recipe(recipe)
    
    print("\n--- Test Execution Logs ---")
    for log in output_log:
        print(log)
    print("---------------------------\n")
    
    # Expected:
    # Inner: 1
    # Inner: 2
    # Outer: A
    # Inner: 1
    # Inner: 2
    # Outer: B
    
    try:
        assert success, "Orchestrator execution failed"
        assert "Outer: A" in output_log, "Outer loop value 'A' was lost!"
        assert "Outer: B" in output_log, "Outer loop value 'B' was lost!"
        print("SUCCESS: Context isolation works perfectly.")
    except AssertionError as e:
        print(f"FAILED assertion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_nested_loops())
