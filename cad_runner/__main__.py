"""Allow ``python -m cad_runner`` from the stable project environment."""

from .cli import main


raise SystemExit(main())
