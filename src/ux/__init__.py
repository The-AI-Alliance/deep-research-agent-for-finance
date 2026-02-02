from typing import Callable, Generic, TypeVar

SYSTEM = TypeVar("SYSTEM")

class Display(Generic[SYSTEM]):
    def __init__(self,
        title: str,
        system: SYSTEM,
        update_iteration_frequency_secs: float = 1.0,
        variables: dict[str,any] = {}):
        self.title = title
        self.system = system
        self.update_iteration_frequency_secs = update_iteration_frequency_secs
        self.variables = variables

    @staticmethod
    def make(
        title: str,
        system: SYSTEM,
        update_iteration_frequency_secs: float = 1.0,
        variables: dict[str,any] = {}):
        """A factory method for creating instances. Subclasses must define one, too."""
        pass

    async def run_live(self, function: Callable[[], None]):
        pass

    def update(self) -> any:
        pass

    def report_results(self, error_msg: str):
        pass

    async def final_update(self, final_messages: list[str]) -> list[any]:
        pass

    def __repl__(self) -> str:
        return f"""title: "{self.title}", update iteration frequency: {self.update_iteration_frequency_secs}"""
    