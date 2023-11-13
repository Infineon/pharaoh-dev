# Define the variable '__version__':
try:
    # See https://github.com/maresb/hatch-vcs-footgun-example
    # If setuptools_scm is installed (e.g. in a development environment with
    # an editable install), then use it to determine the version dynamically.
    from setuptools_scm import get_version

    # This will fail with LookupError if the package is not installed in
    # editable mode or if Git is not installed.
    __version__ = get_version(root="../..", relative_to=__file__)
except (ImportError, LookupError):
    # As a fallback, use the version that is hard-coded in the file.
    try:
        from .version import __version__
    except ModuleNotFoundError:
        # The user is probably trying to run this without having installed
        # the package, so complain.
        msg = "Pharaoh is not correctly installed. Please install it with pip."
        raise RuntimeError(msg) from None
