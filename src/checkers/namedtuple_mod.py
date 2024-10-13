"""typing.NamedTupleMeta mod."""

from __future__ import annotations

import typing


class NamedTupleMeta(type):
    """NamedTuple Metaclass."""

    __slots__ = ()

    def __new__(
        cls: type[NamedTupleMeta],
        typename: str,
        bases: tuple[type, ...],
        ns: dict[str, typing.Any],
    ) -> typing.Any:  # pragma: nocover
        """Create NamedTuple."""
        bases = tuple(tuple if base is typing._NamedTuple else base for base in bases)  # type: ignore[attr-defined]
        for base in bases:
            if tuple not in base.__mro__:
                continue
            break
        else:
            raise ValueError("must subclass tuple somewhere in bases")
        types = ns.get("__annotations__", {})
        default_names = []
        for field_name in types:
            if field_name in ns:
                default_names.append(field_name)
            elif default_names:
                raise TypeError(
                    f"Non-default namedtuple field {field_name} "
                    f"cannot follow default field"
                    f"{'s' if len(default_names) > 1 else ''} "
                    f"{', '.join(default_names)}",
                )
        nm_tpl = typing._make_nmtuple(  # type: ignore[attr-defined]
            typename,
            types.items(),
            defaults=[ns[n] for n in default_names],
            module=ns["__module__"],
        )
        nm_tpl.__bases__ = bases
        if typing.Generic in bases:  # type: ignore[comparison-overlap]
            class_getitem = typing._generic_class_getitem  # type: ignore[attr-defined]
            nm_tpl.__class_getitem__ = classmethod(class_getitem)
        # update from user namespace without overriding special namedtuple attributes
        for key in ns:
            if key in typing._prohibited:  # type: ignore[attr-defined]
                raise AttributeError(
                    "Cannot overwrite NamedTuple attribute " + key,
                )
            if key not in typing._special and key not in nm_tpl._fields:  # type: ignore[attr-defined]
                setattr(nm_tpl, key, ns[key])
        if typing.Generic in bases:  # type: ignore[comparison-overlap]
            nm_tpl.__init_subclass__()
        return nm_tpl


def apply_namedtuple_mod() -> None:  # pragma: nocover
    """Allow NamedTuple to subclass things other than just NamedTuple or Generic."""
    typing.NamedTupleMeta = NamedTupleMeta  # type: ignore[attr-defined]
    typing._NamedTuple = type.__new__(NamedTupleMeta, "NamedTuple", (), {})  # type: ignore[attr-defined]

    def _namedtuple_mro_entries(bases: tuple[type, ...]) -> tuple[type, ...]:
        assert typing.NamedTuple in bases
        return (typing._NamedTuple,)  # type: ignore[attr-defined]

    typing.NamedTuple.__mro_entries__ = _namedtuple_mro_entries  # type: ignore[attr-defined]
