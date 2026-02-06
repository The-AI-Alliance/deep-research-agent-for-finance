from typing import Callable, TypeVar

from dra.common.observer  import Observer

SYSTEM = TypeVar("SYSTEM")

class Display(Observer[SYSTEM]):
    def __init__(self, title: str):
        super().__init__()
        self.title = title        

    async def run_live(self, function: Callable[[], None]):
        """Some displays need to wrap the main system logic, but this should only be done by ONE display."""
        pass
