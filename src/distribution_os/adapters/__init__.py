from .base import AdapterRegistry, PlatformAdapter
from .browser_extension import BrowserExtensionAdapter
from .ebook import EbookAdapter

__all__ = [
    "AdapterRegistry",
    "BrowserExtensionAdapter",
    "EbookAdapter",
    "PlatformAdapter",
]
