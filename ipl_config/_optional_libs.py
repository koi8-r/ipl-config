try:
    import dotenv  # type: ignore[import]
except ImportError:
    dotenv = ImportError(  # type: ignore[no-redef]
        'python-dotenv is not installed'
    )

try:
    import hcl2  # type: ignore[import]
except ImportError:
    hcl2 = ImportError(  # type: ignore[no-redef]
        'python-hcl2 is not installed'
    )

try:
    import toml  # type: ignore[import]
except ImportError:
    toml = ImportError('toml is not installed')  # type: ignore[no-redef]

try:
    import yaml  # type: ignore[import]
except ImportError:
    yaml = ImportError('pyyaml is not installed')  # type: ignore[no-redef]


__all__ = 'dotenv', 'hcl2', 'toml', 'yaml'
