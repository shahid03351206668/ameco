__version__ = "0.0.1"


def _patch_naming():
    try:
        from ameco.naming import apply_patch

        apply_patch()
    except ImportError:
        # frappe is not importable yet (e.g. during packaging)
        pass


_patch_naming()
