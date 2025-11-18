"""
候选人数据模型

版权所有 (c) 2025 赵宏宇
"""
from datetime import datetime
from . import db


class Candidate(db.Model):
    """候选人表"""
    
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    photo_path = db.Column(db.String(500))
    description = db.Column(db.Text)
    votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    vote_records = db.relationship('Vote', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    lottery_records = db.relationship('LotteryRecord', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Candidate {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        # 修复照片路径：确保图片URL正确
        photo_url = self.photo_path
        
        # 如果photo_path为空，返回空字符串
        if not photo_url:
            photo_url = ''
        # 如果photo_path已经是完整路径，直接使用
        elif photo_url.startswith('/uploads/'):
            # 确保路径包含正确的子目录
            if '/photos/' not in photo_url:
                filename = photo_url.replace('/uploads/', '')
                photo_url = f'/uploads/photos/{filename}'
        # 如果photo_path只是文件名，添加完整路径
        elif photo_url and not photo_url.startswith('/'):
            photo_url = f'/uploads/photos/{photo_url}'
        # 如果photo_path是相对路径，转换为绝对路径
        elif photo_url.startswith('uploads/'):
            photo_url = f'/{photo_url}'
        
        return {
            'id': self.id,
            'name': self.name,
            'photo_path': self.photo_path,  # 保持原始photo_path
            'photo_url': photo_url,  # 前端使用photo_url字段
            'description': self.description,
            'votes': self.votes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建候选人"""
        candidate = Candidate(
            name=data.get('name'),
            photo_path=data.get('photo_path'),
            description=data.get('description', '')
        )
        return candidate