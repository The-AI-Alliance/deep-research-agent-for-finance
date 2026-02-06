from typing import Callable, Generic, TypeVar
from common.variables import Variable

SYSTEM = TypeVar("SYSTEM")

class Display(Generic[SYSTEM]):
    def __init__(self,
        title: str,
        system: SYSTEM,
        variables: dict[str, Variable] = {}):
        self.title = title
        self.system = system
        self.variables = variables

    @staticmethod
    def make(
        title: str,
        system: SYSTEM,
        variables: dict[str, Variable] = {}):
        """A factory method for creating instances. Subclasses must define one, too."""
        pass

    async def run_live(self, function: Callable[[], None]):
        pass

    def update(self, final: bool = False) -> any:
        """Pass `final=True` for the last call to update the display before exiting the application."""
        pass

    async def final_update(self, final_messages: list[str], error_msg: str) -> list[any]:
        pass

    def __repl__(self) -> str:
        return f"""title: "{self.title}"""

    # A display loop that will be executed in its own thread.
    async def update_loop(self, update_iteration_frequency_secs: float = 1.0):
        while True:
            try:
                self.display.update()
                await asyncio.sleep(update_iteration_frequency_secs)
            except Exception as e:
                print(f"WARNING: Display update error: {e}")
                break
    
class Displays(Display):
    """A collection of displays, for sending output to multiple locations."""

    def __init__(self,
        title: str,
        system: SYSTEM,
        displays: dict[str, Display] = {},
        variables: dict[str, Variable] = {}):
        super().__init__(title, variables)
        """
        Create a collection of displays to manage as one. 
        The dictionary of displays can't be empty.
        Put the "primary" display in the dictionary first, because it will used alone
        in `run_live`. See its documentation for details.
        """
        if not displays:
            raise ValueError("Displays() called with an empty list of displays!")
        self.displays = displays
        self.first_display = list(self.displays.values())[0]

    @staticmethod
    def make(
        title: str,
        system: SYSTEM,
        make_displays: dict[str, Callable[[SYSTEM, dict[str, Variable]], Display]] = {},
        variables: dict[str, Variable] = {}):
        displays = {}
        for key, func in make_displays.items():
            displays[key] = func(system, variables)
        return Displays(title, system, displays, variables)

    async def run_live(self, function: Callable[[], None]):
        """
        Invokes `run_live(function)` on the FIRST display only, as function is likely to be
        a "singleton"! However, any calls it makes to "display.update()", for example, will
        still go this list of displays and all will be updated.
        """
        await self.first_display.run_live(function)

    def update(self, final: bool = False) -> any:
        """Returns a dict of the results returned from each `display.update()` call."""
        return dict([(key, display.update()) for key, display in self.displays.items()])

    def report_results(self, error_msg: str):
        [display.report_results() for display in self.displays.values()]

    async def final_update(self, final_messages: list[str], error_msg: str) -> list[any]:
        """Returns a list of (key, list) results for all the displays."""
        return [(key, display.final_update(final_messages, error_msg)) \
            for key, display in self.displays.items()]

    def __repl__(self) -> str:
        return "\n".join([f"""Display {key}:\n{display}\n""" for key, display in self.displays.items()])
