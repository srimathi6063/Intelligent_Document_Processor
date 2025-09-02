import logging
import sys

# Optional: coloredlogs for colored output, install via pip if desired:
# pip install coloredlogs
try:
    import coloredlogs
    _HAS_COLOREDLOGS = True
except ImportError:
    _HAS_COLOREDLOGS = False


def setup_logging(level=logging.INFO) -> logging.Logger:
    """
    Setup root logger with console handler and formatter.
    This function returns the configured root logger.

    Args:
        level: Logging level, e.g. logging.DEBUG or logging.INFO.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Avoid adding multiple handlers if already configured
    if not logger.hasHandlers():
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(levelname)-8s %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if _HAS_COLOREDLOGS:
            # Override handlers with coloredlogs if available
            coloredlogs.install(
                level=level,
                logger=logger,
                fmt='[%(asctime)s] %(levelname)-8s %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

    return logger


# Configure logger on import at INFO level by default
logger = setup_logging()
