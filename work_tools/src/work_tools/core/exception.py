class AgentBaseException(Exception):
    """Base class for exceptions raised by agent tools, with optional agent instructions."""

    agent_instruction = ""

    def __init__(self, message=""):
        message = str(message) if message else ""
        if self.agent_instruction and self.agent_instruction not in message:
            if message:
                message = f"{self.agent_instruction}{message}"
            else:
                message = self.agent_instruction.strip()

        super().__init__(message)


class TokenRetrievalError(AgentBaseException):
    """Raised when auth token cannot be retrieved from Chrome."""

    agent_instruction = (
        "[AGENT INSTRUCTION] This is an environment/browser state issue. "
        "DO NOT debug the code or investigate internal logic. "
        "Report the error to the user and ask them to verify their Chrome state (tabs, login, permissions).\n\n"
    )


class TokenExpiredError(AgentBaseException):
    """Raised when an API request fails due to an expired or invalid auth token."""

    agent_instruction = "[AGENT INSTRUCTION] The user must refresh the session in the browser manually.\n\n"
