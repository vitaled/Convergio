"""
Convergio models package.

Intentionally no side-effect imports to avoid duplicate table definitions when
packages are imported via both 'models.*' and 'src.models.*'. Import specific
models from their modules, e.g.:

from models.activity import Activity
from models.cost_tracking import CostTracking
"""

__all__ = []