"""muthmills: the Muth-Mills monocentric city as a solver, comparative-statics and valuation toolkit."""
from loguru import logger

from .city import City, Spec, solve
from .primitives import CobbDouglas, CobbDouglasTech, StoneGeary

__all__ = ["City", "Spec", "solve", "CobbDouglas", "CobbDouglasTech", "StoneGeary"]

logger.disable("muthmills")   # library convention: callers opt in with logger.enable("muthmills")
