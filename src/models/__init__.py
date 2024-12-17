import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from .base_model import Base
from .news_tag_model import NewsModel
from .favorites_model import FavoritesModel
from .categories_model import InterestsModel
from .user_model import UserModel