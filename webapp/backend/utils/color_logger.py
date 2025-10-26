"""
Colored logging utility for comprehensive tool call tracking.
"""

import logging
from typing import Optional, Dict, Any, List


class ColorCodes:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = '\033[0m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


class ToolCallFormatter(logging.Formatter):
    """Custom formatter for tool call logging with colors."""

    COLORS = {
        'DEBUG': ColorCodes.BRIGHT_BLACK,
        'INFO': ColorCodes.CYAN,
        'WARNING': ColorCodes.YELLOW,
        'ERROR': ColorCodes.RED,
        'CRITICAL': ColorCodes.RED + ColorCodes.BG_WHITE,
    }

    PREFIX_COLORS = {
        'TOOL_CALL_START': ColorCodes.BRIGHT_CYAN,
        'TOOL_CALL_END': ColorCodes.BRIGHT_GREEN,
        'TOOL_CALL_ERROR': ColorCodes.BRIGHT_RED,
        'TOOL_EXEC_START': ColorCodes.BRIGHT_MAGENTA,
        'TOOL_EXEC_END': ColorCodes.BRIGHT_MAGENTA,
        'TOOL_VALIDATION': ColorCodes.BRIGHT_YELLOW,
        'TOOL_ORCHESTRATION': ColorCodes.BRIGHT_BLUE,
        'LLM_TOOL_REQUEST': ColorCodes.BRIGHT_CYAN,
        'LLM_TOOL_RESPONSE': ColorCodes.BRIGHT_GREEN,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Get color based on level
        level_color = self.COLORS.get(record.levelname, '')

        # Extract prefix and apply prefix color if present
        message = record.getMessage()
        prefix = None
        prefix_color = None

        for key, color in self.PREFIX_COLORS.items():
            if message.startswith(f"[{key}]"):
                prefix = key
                prefix_color = color
                message = message.replace(
                    f"[{key}]", f"[{ColorCodes.RESET}{key}{level_color}]")
                break

        # Apply level color
        levelname_colored = f"{level_color}{record.levelname:<8}{ColorCodes.RESET}"

        # Format the record
        formatted = f"{levelname_colored} {message}"

        return formatted


def setup_tool_logging(logger_name: str = None) -> logging.Logger:
    """
    Set up colored logging for tool calls.

    Args:
        logger_name: Name of logger to configure

    Returns:
        Configured logger
    """
    logger = logging.getLogger(logger_name or __name__)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Create handler
    handler = logging.StreamHandler()
    handler.setFormatter(ToolCallFormatter('%(levelname)s %(message)s'))

    # Set level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def log_tool_call_start(
    logger: logging.Logger,
    call_id: str,
    tool_name: str,
    arguments: Dict[str, Any],
    execution_mode: str
):
    """Log start of tool call proposal."""
    # Extract key parameters
    operation = arguments.get('operation', 'N/A')
    path = arguments.get('path', 'N/A')
    
    logger.info(
        f"[TOOL_CALL_START] Proposing tool call: {call_id}"
    )
    logger.info(f"[TOOL_CALL_START] Tool: {tool_name} | Operation: {operation}")
    logger.info(f"[TOOL_CALL_START] Path: {path} | Mode: {execution_mode}")
    
    # Log value if present (for append/upsert operations)
    if 'value' in arguments and arguments['value'] is not None:
        value_preview = str(arguments['value'])[:200]  # Limit length
        if len(str(arguments['value'])) > 200:
            value_preview += "..."
        logger.info(f"[TOOL_CALL_START] Value: {value_preview}")
    
    # Log full arguments at DEBUG level
    logger.debug(f"[TOOL_CALL_START] Full arguments: {arguments}")


def log_tool_call_validated(
    logger: logging.Logger,
    call_id: str,
    validation_errors: List[str]
):
    """Log tool call validation result."""
    if validation_errors:
        logger.warning(
            f"[TOOL_VALIDATION] Tool call {call_id} has {len(validation_errors)} validation error(s)"
        )
        for error in validation_errors:
            logger.warning(f"[TOOL_VALIDATION] {error}")
    else:
        logger.info(f"[TOOL_VALIDATION] Tool call {call_id} passed validation")


def log_tool_call_executing(
    logger: logging.Logger,
    call_id: str,
    tool_name: str,
    operation: Optional[str] = None
):
    """Log start of tool call execution."""
    logger.info(f"[TOOL_EXEC_START] Executing tool call: {call_id}")
    logger.info(f"[TOOL_EXEC_START] Tool: {tool_name}")
    if operation:
        logger.info(f"[TOOL_EXEC_START] Operation: {operation}")


def log_tool_call_success(
    logger: logging.Logger,
    call_id: str,
    result: Dict[str, Any]
):
    """Log successful tool call completion."""
    logger.info(
        f"[TOOL_CALL_END] Tool call {call_id} completed successfully"
    )

    # Log result summary
    if result.get('ok') is not False:
        if 'diff' in result and result.get('diff'):
            logger.info(
                f"[TOOL_CALL_END] Generated {len(result.get('diff', []))} diff item(s)"
            )
        if 'metrics' in result:
            metrics = result['metrics']
            if 'ownership' in metrics:
                logger.info(
                    f"[TOOL_CALL_END] Metrics computed for {len(metrics['ownership'])} holders"
                )


def log_tool_call_failure(
    logger: logging.Logger,
    call_id: str,
    error: str
):
    """Log failed tool call."""
    logger.error(f"[TOOL_CALL_ERROR] Tool call {call_id} failed: {error}")


def log_llm_tool_request(
    logger: logging.Logger,
    tool_name: str,
    arguments: Dict[str, Any]
):
    """Log LLM tool request."""
    logger.info(
        f"[LLM_TOOL_REQUEST] LLM requested: {tool_name}"
    )
    logger.debug(f"[LLM_TOOL_REQUEST] Arguments: {arguments}")


def log_llm_tool_response(
    logger: logging.Logger,
    call_id: str,
    status: str,
    result_summary: Optional[str] = None
):
    """Log LLM tool response."""
    logger.info(
        f"[LLM_TOOL_RESPONSE] Tool call {call_id} - Status: {status}"
    )
    if result_summary:
        logger.info(f"[LLM_TOOL_RESPONSE] {result_summary}")


def log_orchestration_event(
    logger: logging.Logger,
    event: str,
    call_id: str,
    details: Optional[str] = None
):
    """Log orchestration event."""
    logger.info(f"[TOOL_ORCHESTRATION] {event} | Call ID: {call_id}")
    if details:
        logger.debug(f"[TOOL_ORCHESTRATION] {details}")

