"""Keep standalone PiFlow imports from creating the legacy default log file."""
import logging
import os

# Stage events are persisted by the extension. An already configured host logger is kept.
if os.getenv("FORECAST_WITH_LEGACY") != "1" and not logging.getLogger("piflow").handlers:
    logging.getLogger("piflow").addHandler(logging.NullHandler())
