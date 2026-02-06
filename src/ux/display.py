from typing import Callable
from common.observer  import Observer
from common.variables import Variable

class Display(Observer):
    def __init__(self,
        title: str,
        system: SYSTEM,
        variables: dict[str, Variable] = {}):
        super().__init__(title, system, variables)

    async def run_live(self, function: Callable[[], None]):
        """Some displays need to wrap the main system logic, but this should only be done by ONE display."""
        pass
