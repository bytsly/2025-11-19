"""
投票配置数据模型

版权所有 (c) 2025 赵宏宇
"""
from . import db


class VoteConfig(db.Model):
    """投票配置表"""
    
    __tablename__ = 'vote_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    vote_name = db.Column(db.String(200), default="投票活动", nullable=False, comment="投票活动名称")
    max_votes_per_user = db.Column(db.Integer, default=1, nullable=False, comment="每个用户最大投票数")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), 
                          onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<VoteConfig max_votes={self.max_votes_per_user}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'vote_name': self.vote_name,
            'max_votes_per_user': self.max_votes_per_user,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_config():
        """获取投票配置（单例模式）"""
        config = VoteConfig.query.first()
        if not config:
            # 创建默认配置
            config = VoteConfig(vote_name="投票活动", max_votes_per_user=1)
            db.session.add(config)
            db.session.commit()
        return config
    
    @staticmethod
    def update_config(vote_name=None, max_votes_per_user=None):
        """更新投票配置"""
        config = VoteConfig.get_config()
        if vote_name is not None:
            config.vote_name = vote_name
        if max_votes_per_user is not None:
            config.max_votes_per_user = max_votes_per_user
        db.session.commit()
        return config