import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Directory for logs
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | [%(name)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(
    name: str,
    log_file: str,
    to_stderr: bool = False,
    level: int = None
) -> logging.Logger:
    """
    Sets up and returns a robust logger configured with both rotating file output and console output.
    
    Args:
        name: Name of the logger (e.g. 'mcp.server', 'agent').
        log_file: Filename in the logs/ directory (e.g. 'filesystem_server.log').
        to_stderr: If True, console logs are directed to sys.stderr (CRITICAL for MCP servers on stdio).
                   If False, directed to sys.stdout.
        level: Optional log level override. Defaults to LOG_LEVEL env var or logging.INFO.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    # Determine log level from env or argument
    if level is None:
        env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)
    
    logger.setLevel(level)

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DATE_FORMAT)

    # 1. Rotating File Handler (UTF-8 encoded to handle Unicode cleanly)
    file_path = LOGS_DIR / log_file
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 2. Console Handler (stderr for MCP server so stdio JSON-RPC is never corrupted)
    stream = sys.stderr if to_stderr else sys.stdout
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger if already handled
    logger.propagate = False

    return logger
