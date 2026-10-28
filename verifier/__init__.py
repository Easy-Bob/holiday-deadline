"""The deterministic verifier: each tool's checks, and the task's, on contract instances."""

from contract import Task, Tool

from . import task
from .tools import Holidays, Month, Pin

TOOLS = {
    Tool.PIN_HOLIDAYS: Pin,
    Tool.PUBLIC_HOLIDAYS: Holidays,
    Tool.CALENDAR: Month,
}

# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {
    Task.FIND_DEADLINE: task.verify_task,
}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
