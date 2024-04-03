__version__ = "0.1.1"


from . import datasystems as datasystems
from . import exceptions as exceptions
from . import mailsystems as mailsystems
from . import platforms as platforms
from .abstract import AbstractDataSystem as AbstractDataSystem
from .abstract import AbstractItem as AbstractItem
from .abstract import AbstractMailSystem as AbstractMailSystem
from .abstract import AbstractMessage as AbstractMessage
from .abstract import AbstractPlatform as AbstractPlatform
from .core import iter_items_to_cancel as iter_items_to_cancel
