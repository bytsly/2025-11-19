"""
抽奖记录数据模型

版权所有 (c) 2025 赵宏宇
"""
from datetime import datetime
from . import db


class LotteryRecord(db.Model):
    """抽奖记录表"""
    
    __tablename__ = 'lottery_records'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    round = db.Column(db.Integer, nullable=False, index=True)  # 抽奖轮次
    prize_name = db.Column(db.String(100))  # 奖项名称
    drawn_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<LotteryRecord round={self.round} candidate={self.candidate_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'candidate_name': self.candidate.name if self.candidate else '未知',
            'round': self.round,
            'prize_name': self.prize_name,
            'drawn_at': self.drawn_at.isoformat() if self.drawn_at else None
        }
    
    @staticmethod
    def get_max_round():
        """获取当前最大轮次"""
        max_round = db.session.query(db.func.max(LotteryRecord.round)).scalar()
        return max_round or 0
    
    @staticmethod
    def get_winners_ids():
        """获取所有中奖者ID列表"""
        winners = db.session.query(LotteryRecord.candidate_id).distinct().all()
        return [w[0] for w in winners]