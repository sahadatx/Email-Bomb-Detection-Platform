from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModuleDefinition:
    """
    Registered backend module metadata.
    """

    name: str
    router: Any
    prefix: str
    tags: tuple[str, ...] = field(default_factory=tuple)


class ModuleRegistry:
    """
    Central registry for application modules.
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleDefinition] = {}

    def register(
        self,
        *,
        name: str,
        router: Any,
        prefix: str,
        tags: list[str] | tuple[str, ...] = (),
    ) -> None:
        if name in self._modules:
            raise ValueError(
                f"Module '{name}' is already registered."
            )

        self._modules[name] = ModuleDefinition(
            name=name,
            router=router,
            prefix=prefix,
            tags=tuple(tags),
        )

    def get(
        self,
        name: str,
    ) -> ModuleDefinition | None:
        return self._modules.get(name)

    def all(self) -> tuple[ModuleDefinition, ...]:
        return tuple(self._modules.values())

    def clear(self) -> None:
        self._modules.clear()


module_registry = ModuleRegistry()