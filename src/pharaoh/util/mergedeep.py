from __future__ import annotations


def merge(a, b, safe=True, path=None):
    """
    Merges dict b into dict a.

    :param a: Mutable dict. This will be the merge target.
    :param b: This will be the merge source.
    :param safe: If True, existing keys will not be overwritten and a KeyExistsError will be raised.
    :param path: Shall be None for users, used for recursion of the function.
    """
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], safe, [*path, str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                if safe:
                    msg = f"Conflict at {'.'.join([*path, str(key)])}. Only unique keys are allowed!"
                    raise Exception(msg)
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a
