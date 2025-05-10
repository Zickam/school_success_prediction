import logging
import logging.handlers as handlers
import os
from pathlib import Path

def init(file_path: str = None):
    """Initialize logging configuration"""
    # Use environment variable if set
    if file_path is None:
        file_path = os.environ.get("APP_LOG_PATH", "logs/app.log")
    log_dir = os.path.dirname(file_path)
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create handlers
    file_handler = handlers.TimedRotatingFileHandler(
        file_path,
        backupCount=32,
        when="midnight"
    )
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set logging level for specific modules
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING) 