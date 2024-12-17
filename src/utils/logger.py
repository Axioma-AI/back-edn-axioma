import logging
import coloredlogs
import os

def setup_logger(name, level=logging.INFO, log_file='app.log'):
    """
    Sets up a logger with the given name and level, and adds colored logs.
    
    Args:
        name (str): The name of the logger.
        level (int): The logging level.
        log_file (str): The file where logs will be saved.
        
    Returns:
        logging.Logger: The configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a file handler
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = logging.FileHandler(os.path.join('logs', log_file), encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = coloredlogs.ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
