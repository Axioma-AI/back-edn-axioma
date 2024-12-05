import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from fastapi import APIRouter
from . import articles
from . import analysis
from . import categories
from . import favorites

router = APIRouter()
# router.include_router(articles.router)
router.include_router(articles.router)
router.include_router(analysis.router)
router.include_router(categories.router)
router.include_router(favorites.router)