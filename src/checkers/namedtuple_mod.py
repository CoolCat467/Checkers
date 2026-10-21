"""typing.NamedTupleMeta mod."""

from __future__ import annotations

import typing

import _typing
import mypy_extensions


@mypy_extensions.mypyc_attr(native_class=False)
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
        bases = tuple(
            tuple if base is typing._NamedTuple else base  # type: ignore[attr-defined]
            for base in bases
        )
        if "__annotations__" in ns:
            types = ns["__annotations__"]
            field_names = list(types)
            annotate = typing._make_eager_annotate(types)  # type: ignore[attr-defined]
        elif (
            original_annotate
            := typing._lazy_annotationlib.get_annotate_from_class_namespace(ns)  # type: ignore[attr-defined]
        ) is not None:
            types = typing._lazy_annotationlib.call_annotate_function(  # type: ignore[attr-defined]
                original_annotate,
                typing._lazy_annotationlib.Format.FORWARDREF,  # type: ignore[attr-defined]
            )
            field_names = list(types)

            # For backward compatibility, type-check all the types at creation time
            for typ in types.values():
                typing._type_check(typ, "field annotation must be a type")  # type: ignore[attr-defined]

            def annotate(
                format_: typing._lazy_annotationlib.Format,  # type: ignore[name-defined]
            ) -> dict[str, type]:
                annos = typing._lazy_annotationlib.call_annotate_function(  # type: ignore[attr-defined]
                    original_annotate,
                    format_,
                )
                if format_ != typing._lazy_annotationlib.Format.STRING:  # type: ignore[attr-defined]
                    return {
                        key: typing._type_check(  # type: ignore[attr-defined]
                            val,
                            f"field {key} annotation must be a type",
                        )
                        for key, val in annos.items()
                    }
                return annos  # type: ignore[no-any-return]
        else:
            # Empty NamedTuple
            field_names = []

            def annotate(
                format_: typing._lazy_annotationlib.Format,  # type: ignore[name-defined]
            ) -> dict[str, type]:
                return {}

        default_names = []
        for field_name in field_names:
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
            field_names,
            annotate,
            defaults=[ns[n] for n in default_names],
            module=ns["__module__"],
        )
        nm_tpl.__bases__ = bases
        if typing.Generic in bases:
            class_getitem = _typing.Generic_class_getitem
            nm_tpl.__class_getitem__ = classmethod(class_getitem)
        # update from user namespace without overriding special namedtuple attributes
        for key, val in ns.items():
            if key in typing._prohibited:  # type: ignore[attr-defined]
                raise AttributeError(
                    "Cannot overwrite NamedTuple attribute " + key,
                )
            if key not in typing._special:  # type: ignore[attr-defined]
                if key not in nm_tpl._fields:
                    setattr(nm_tpl, key, val)
                try:
                    set_name = type(val).__set_name__
                except AttributeError:
                    pass
                else:
                    try:
                        set_name(val, nm_tpl, key)
                    except BaseException as e:
                        e.add_note(
                            f"Error calling __set_name__ on {type(val).__name__!r} "
                            f"instance {key!r} in {typename!r}",
                        )
                        raise

        if typing.Generic in bases:
            nm_tpl.__init_subclass__()
        return nm_tpl


# def apply_namedtuple_mod() -> None:  # pragma: nocover
#     """Allow NamedTuple to subclass things other than just NamedTuple or Generic."""
#     typing.NamedTupleMeta = NamedTupleMeta  # type: ignore[attr-defined]
#     typing._NamedTuple = type.__new__(NamedTupleMeta, "NamedTuple", (), {})  # type: ignore[attr-defined]
#
#     def _namedtuple_mro_entries(bases: tuple[type, ...]) -> tuple[type, ...]:
#         assert typing.NamedTuple in bases
#         return (typing._NamedTuple,)  # type: ignore[attr-defined]
#
#     typing.NamedTuple.__mro_entries__ = _namedtuple_mro_entries  # type: ignore[attr-defined]
