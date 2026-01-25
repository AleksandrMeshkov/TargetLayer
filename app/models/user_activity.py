# This file is kept for backward compatibility
# UserActivity has been renamed to UserRoadmap
# Please use: from app.models.user_roadmap import UserRoadmap

from app.models.user_roadmap import UserRoadmap as UserActivity

__all__ = ["UserActivity"]
