"""
投票记录数据模型

版权所有 (c) 2025 赵宏宇
"""
from datetime import datetime
from . import db


class Vote(db.Model):
    """投票记录表"""
    
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    voter_ip = db.Column(db.String(45), nullable=False, index=True)
    device_fingerprint = db.Column(db.String(255), index=True)
    user_agent = db.Column(db.String(500))
    voted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Vote candidate_id={self.candidate_id} ip={self.voter_ip}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'candidate_name': self.candidate.name if self.candidate else None,
            'voter_ip': self.voter_ip,
            'device_fingerprint': self.device_fingerprint,
            'voted_at': self.voted_at.isoformat() if self.voted_at else None
        }
    
    @staticmethod
    def has_voted(ip, fingerprint=None):
        """检查是否已投票"""
        # 根据IP地址和设备指纹检查是否已投票
        query = Vote.query.filter_by(voter_ip=ip)
        if fingerprint:
            query = query.filter_by(device_fingerprint=fingerprint)
        return query.first() is not None
    
    @staticmethod
    def get_vote_count_by_ip(ip, fingerprint=None):
        """获取IP投票次数"""
        # 根据IP地址和设备指纹统计投票次数
        query = Vote.query.filter_by(voter_ip=ip)
        if fingerprint:
            query = query.filter_by(device_fingerprint=fingerprint)
        return query.count()
    
    @staticmethod
    def get_votes_by_user(ip, fingerprint=None):
        """获取用户自己的投票记录"""
        # 根据IP地址和设备指纹获取用户的投票记录
        query = Vote.query.filter_by(voter_ip=ip)
        if fingerprint:
            query = query.filter_by(device_fingerprint=fingerprint)
        return query.order_by(Vote.voted_at.desc()).all()
