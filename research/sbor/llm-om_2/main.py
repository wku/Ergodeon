import os
import json
import logging
from config import BASE_WORKDIR, EPISODES_FILE
from agent import Agent

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)


def main():
    print(f"luxion agent")
    print(f"workspace: {os.path.abspath(BASE_WORKDIR)}")
    print(f"memory: {os.path.abspath(EPISODES_FILE)}")
    print("type 'exit' to quit\n")

    agent = Agent()

    while True:
        try:
            goal = input("goal> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break
        if not goal:
            continue
        if goal.lower() in ("exit", "quit"):
            break
        res = agent.run_episode(goal)
        print(f"\n[result] {json.dumps(res, indent=2, ensure_ascii=False)}\n")


if __name__ == "__main__":
    main()
