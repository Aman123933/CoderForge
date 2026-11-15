from backend.app.memory.state_store import StateStore
from backend.app.tools.execution_tools import SafePythonExecutor



class RunnerAgent:
    def __init__(
        self,
        intent_agent,
        planner_agent,
        architect_agent,
        coder_agent,
        reviewer_agent,
    ):
        self.intent_agent = intent_agent
        self.planner_agent = planner_agent
        self.architect_agent = architect_agent
        self.coder_agent = coder_agent
        self.reviewer_agent = reviewer_agent
        self.memory = StateStore()
        self.executor = SafePythonExecutor()


    def run(self, user_prompt: str):
        self.memory.clear()

        intent = self.intent_agent.extract_intent(user_prompt)
        self.memory.set("intent", intent)

        plan = self.planner_agent.create_plan(intent)
        self.memory.set("plan", plan)

        architecture = self.architect_agent.design_architecture(plan)
        self.memory.set("architecture", architecture)

        file_spec = {
            "file_path": "backend/app/main.py",
            "file_purpose": "Application entry point",
            "requirements": [
                "Initialize application",
                "Expose health endpoint"
            ]
        }

        code = self.coder_agent.generate_code(file_spec)
        self.memory.set("code", code)

        review = self.reviewer_agent.review_code(
            code=code,
            architecture_context=architecture
        )
        
        self.memory.set("review", review)
        execution_result = None

        if not review.get("issues"):
            execution_result = self.executor.execute(code)
            self.memory.set("execution", execution_result)
        else:
            self.memory.set("execution", None)


        return self.memory.all()
