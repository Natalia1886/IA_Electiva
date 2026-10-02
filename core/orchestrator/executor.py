"""Ejecuta el plan de agentes y skills, maneja excepciones y trazabilidad."""

from typing import Dict, Any
from core.orchestrator.router import Router
from core.orchestrator.planner import Planner
from core.observability.logger import get_logger
from core.observability.tracer import tracer

logger = get_logger("orchestrator.executor")


class Executor:
    """Orquestador ejecutor principal."""

    def __init__(self):
        self.router = Router()
        self.planner = Planner()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una tarea asignándole el agente correspondiente según el plan."""
        intent = task.get("intent", "unknown")
        tracer.log_event("task_start", "orchestrator", {"intent": intent})

        agent = self.router.get_agent_instance(task)
        if not agent:
            err_msg = f"No se pudo resolver agente ejecutor para tarea con intent: '{intent}'"
            logger.error(err_msg)
            tracer.log_event("task_error", "orchestrator", {"error": err_msg})
            return {"status": "error", "message": err_msg, "data": None}

        plan = self.planner.create_plan(task)
        tracer.log_event("plan_created", agent.name, {"plan": plan})

        try:
            task["_plan"] = plan
            result = agent.run(task)
            tracer.log_event("task_complete", agent.name, {"status": "success"})
            return {"status": "success", "agent": agent.name, "result": result}
        except Exception as e:
            logger.exception(f"Falla durante la ejecución del agente '{agent.name}': {e}")
            tracer.log_event("task_exception", agent.name, {"error": str(e)})
            return {"status": "error", "agent": agent.name, "error": str(e)}
