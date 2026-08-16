from dotenv import load_dotenv
from graph.graph import build_graph

load_dotenv()


def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + "AutoDev".center(58) + "║")
    print("║" + "Autonomous Coding Agent".center(58) + "║")
    print("╠" + "═" * 58 + "╣")
    print("║  Describe your coding task to get started.              ║")
    print("║  Type 'quit' or 'exit' to close the agent.              ║")
    print("╚" + "═" * 58 + "╝")
    print()


    graph = build_graph()

    while True:
        task = input("\nYour Task here: ").strip()

        if not task:
            continue
        if task.lower() in {"quit", "exit", "q", "cya"}:
            print("BYE!")
            break

        start_state = {
            "task": task,
            "code": "",
            "tests": "",
            "test_results":"",
            "error": "",
            "retry_count":0,
            "status": "running"
        }

        end_state = graph.invoke(start_state)

        # Print result
        print()
        print("╔" + "═" * 58 + "╗")

        if end_state["status"] == "pass":
            print("║" + "BUILD SUCCESSFUL".center(58) + "║")
            print("╠" + "═" * 58 + "╣")
            print("║  end code:" + " " * 45 + "║")
            print("╚" + "═" * 58 + "╝")
            print()
            print(end_state["code"])

        elif end_state["status"] == "escalate":
            print("║" + "ESCALATION REQUIRED".center(58) + "║")
            print("╠" + "═" * 58 + "╣")
            print("║  Agents were unable to resolve the issue." + " " * 15 + "║")
            print("╚" + "═" * 58 + "╝")
            
            print("\nLast code:")
            print("-" * 60)
            print(end_state["code"])

            print("\nLast error:")
            print("-" * 60)
            print(end_state["error"])

        print()


if __name__ == "__main__":
    main()