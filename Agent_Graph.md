[User Task]
     ↓
[Coder Agent] → generates code
     ↓
[Tester Agent] → generates tests
     ↓
[Execution Tool] → actually RUNS the code
     ↓
  Did it pass?
  /          \
YES           NO
 ↓             ↓
[Done]    [Back to Coder] ← (with the error message!)
                ↓
           (tries again)
                ↓
      Tried 3 times? → [Human Escalation]
