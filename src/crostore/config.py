import os

PREFIX = "CROSTORE_"


SELENIUM_WAIT = int(os.environ.get(PREFIX + "SELENIUM_WAIT", "10"))
