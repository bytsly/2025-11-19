"""
数据模型包

版权所有 (c) 2025 赵宏宇
"""
from flask_sqlalchemy import SQLAlchemy

# 创建数据库对象
db = SQLAlchemy()

# 延迟导入以避免循环依赖
from .candidate import Candidate
from .vote import Vote
from .lottery import LotteryRecord
from .vote_config import VoteConfig
from .admin import AdminUser

__all__ = ['db', 'Candidate', 'Vote', 'LotteryRecord', 'VoteConfig', 'AdminUser']
