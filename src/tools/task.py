from task import TaskManager
from llm.types import Tool

TASK_CREATE_TOOL_DEFINITION = Tool(
    name="task_create",
    description="Create a new task in the plan. Returns the task ID.",
    input_schema={
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "Description of the task to create",
            },
        },
        "required": ["description"],
    },
)

TASK_UPDATE_TOOL_DEFINITION = Tool(
    name="task_update",
    description=(
        'Update the status of an existing task. '
        'Status can be "pending", "in_progress", "completed", or "failed".'
    ),
    input_schema={
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The task ID to update",
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "failed"],
                "description": "The new status for the task",
            },
        },
        "required": ["id", "status"],
    },
)

TASK_LIST_TOOL_DEFINITION = Tool(
    name="task_list",
    description=(
        "List all tasks in the current plan with their status. "
        "Optionally filter by status."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "failed"],
                "description": "Filter tasks by status (optional)",
            },
        },
    },
)

TASK_TOOLS = [
    TASK_CREATE_TOOL_DEFINITION,
    TASK_UPDATE_TOOL_DEFINITION,
    TASK_LIST_TOOL_DEFINITION,
]



def execute_task_tool(manager: TaskManager, name: str, input: dict) -> str:
    if name == "task_create":
        description = input.get("description")
        if not description:
            return "Error: Task tool description is required"

        task_id = manager.create(description)
        return f"Created {task_id}: {description}"

    if name == "task_update":
        task_id = input.get("id", )
        status = input.get("status")
        if not task_id:
            return "Error: Task tool id is required"
        if not status:
            return "Error: Task tool status is required"

        ok = manager.update(task_id, status)
        if not ok:
            return f"Error: Task {task_id} not found"

        return f"Updated {task_id} status to {status}"

    if name == "task_list":
        status = input.get("status")
        tasks = manager.list(status)
        if not tasks:
            return "(no tasks)"

        return "\n".join(
            f"{task.id} [{task.status}]: {task.description}"
            for task in tasks
        )


    return f"Error: Unknown task tool: {name}"
