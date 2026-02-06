from typing import Callable, Generic, TypeVar
from common.variables import Variable

SYSTEM = TypeVar("SYSTEM")

class Observer(Generic[SYSTEM]):
    def __init__(self,
        title: str,
        system: SYSTEM,
        variables: dict[str, Variable] = {}):
        self.title = title
        self.system = system
        self.variables = variables

    def update(self, final: bool = False, messages: list[str] = [], error_msg: str = None) -> any:
        """Pass `final=True` for the last call to update the observer before exiting the application."""
        pass

    def __repl__(self) -> str:
        return f"""title: "{self.title}"""
    
class Observers(Observer):
    """A collection of observers, for transparently managing updates for multiple recipients."""

    def __init__(self,
        title: str,
        system: SYSTEM,
        observers: dict[str, Observer] = {},
        variables: dict[str, Variable] = {}):
        super().__init__(title, variables)
        """
        Create a collection of observers to manage as one. 
        The dictionary of observers can't be empty.
        Put the "primary" observer in the dictionary first, because it will used alone
        in `run_live`. See its documentation for details.
        """
        if not observers:
            raise ValueError("Observers() called with an empty list of observers!")
        self.observers = observers
        self.first_observer = list(self.observers.values())[0]

    def update(self, final: bool = False, messages: list[str] = [], error_msg: str = None) -> any:
        """Returns a dict of the results returned from each `observer.update()` call."""
        d = {}
        for key, observer in self.observers.items():
            d[key] = observer.update(final=final, messages=messages, error_msg=error_msg)
        return d

    def __repl__(self) -> str:
        return "\n".join([f"""{key}:\n{observer}\n""" for key, observer in self.observers.items()])
