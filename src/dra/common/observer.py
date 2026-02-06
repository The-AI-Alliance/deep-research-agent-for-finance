from typing import Callable, Generic, TypeVar
from dra.common.variables import Variable

SYSTEM = TypeVar("SYSTEM")

class Observer(Generic[SYSTEM]):
    """
    Observe a "system" as its state changes.
    An observer can be constructed with `None` as the system, in which
    case nothing will happen until `update(system = ...)` is called with
    a non-None sysetm.
    """
    def __init__(self):
        """
        Initialize the observer. Note that the system observed is not specified here,
        but rather in the first call to `update()`. This makes order of initialization,
        especially in class hierarchies, more robust.
        """
        self.system: SYSTEM = None
        self.resume()

    def update(self, 
        system: SYSTEM = None,
        other: dict[str,any] = {},
        is_final: bool = False) -> any:
        """
        Update the observer with a possibly-new system to observe. See also 
        `_before_set_system()` and `_after_set_system()`.

        Args:
            system (SYSTEM): If not `None` and not equal to `self.system`, then `self.system` is assigned to it.
            other (dict[str,any]): Is a hook to provide additional data to observers that is is transparent to this class.
            is_final (bool): Pass `True` for the last call to update the observer before the application exits.

        Returns:
            any: The return value is up to derived classes. We return `None` if `self.system != None` and we aren't paused, or the returned value from `_do_update()`.

        Discussion:
            Derived classes should only override _do_update(), which is called only if `self.system != None` and we aren't paused.
        """
        self.__update_system(system)
        if self.system and not self.paused:
            return self._do_update(other, is_final)
        else:
            return None

    def _do_update(self, 
        other: dict[str,any] = {},
        is_final: bool = False) -> any:
        """
        Derived classes override this method for customizing update logic. This method is only
        called if `self.system != None` and we aren't paused, so it is safe to do any update
        processing.

        Args:
            is_final (bool): Pass `True` for the last call to update the observer before the application exits.
            messages (list[str]): Option messages the observer can use. Most often used on the final call for user notification.
            error_msg (str): Option message about an error the observer can use. Most often used on the final call for user notification.
        """
        pass

    def __update_system(self, new_system: SYSTEM):
        if new_system and new_system != self.system:
            if self.system: # old system not None?
                self._before_set_system()
            self.system = new_system
            self._after_set_system()

    def _before_set_system(self):
        """
        A hook for derived classes to override _before_ `self.system` is changed.
        Override this method if resources need to be recovered (e.g.,
        close open files). 
        This method is called even if `self.paused == True`. However, 
        this method isn't called if the old `self.system` is `None`. 
        """
        pass

    def _after_set_system(self):
        """
        A hook for derived classes to override _after_ the system has been changed.
        This method will always be called at least once for an observer during the first
        invocation of `update()`. Hence, this is the place to do any required initialization
        and it is generally safer doing it after a class hierarchy's `__init__()` methods 
        have finished.
        This method is called even if `self.paused == True`. However, 
        this method isn't called if `self.system` is `None`. 
        """
        pass

    def pause(self):
        """Pause update processing"""
        self.paused = True

    def resume(self):
        """Resume update processing"""
        self.paused = False

    def __repl__(self) -> str:
        return ''
    
class Observers(Observer):
    """
    A collection of observers, for transparently managing updates to multiple 
    observers from the same system.
    """

    def __init__(self, observers: dict[str, Observer] = {}):
        super().__init__()
        """
        Create a collection of observers to manage as one. 
        The dictionary of observers can't be empty.
        """
        if not observers:
            raise ValueError("Observers() called with an empty list of observers!")
        self.observers = observers

    def _do_update(self, 
        other: dict[str,any] = {},
        is_final: bool = False) -> any:
        """Returns a dict of the results returned from each `observer.update()` call."""
        d = {}
        for key, observer in self.observers.items():
            d[key] = observer.update(system=self.system, other=other, is_final=is_final)
        return d

    def pause(self):
        """
        Pause update processing for all the member observers.
        Even if a member observer is not paused, it won't get updated by this class's `update()` call.
        """
        super().pause()

    def resume(self):
        """
        Resume update processing for all this object's observers.
        If a member observer is paused, its `update()` will be called now, but its
        own pause setting will prevent updates.
        """
        super().resume()

    def __repl__(self) -> str:
        return "\n".join([f"""{key}:\n{observer}\n""" for key, observer in self.observers.items()])
