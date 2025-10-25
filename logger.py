import logging
import re
from datetime import datetime

class PIIFilter(logging.Filter):
    # Regex to strip PII (emails, IDs, etc.)
    PII_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', # Emails
        r'\d{3}-\d{2}-\d{4}', # SSNs (example)
        r'\b\d{16}\b', # Card numbers
    ]

    def filter(self, record):
        if 'data' in record.__dict__:
            for pattern in self.PII_PATTERNS:
                record.__dict__['data'] = re.sub(pattern, '[REDACTED]', str(record.__dict__['data']))
        return True
    
logger = logging.getLogger('secure_logger')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.addFilter(PIIFilter())
formatter = logging.Formatter('%(asctime)s - %(names)s - %(levelname)s - %(message)s - Extra: %(extra)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class SecureLogger:
    def info(self, msg, extra=None):
        logger.info(msg, extra=extra or {})
    
    def warning(self, msg, extra=None):
        logger.warning(msg, extra=extra or {})

    def error(self, msg, extra=None):
        logger.error(msg, extra=extra or {})