from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class ChannelValidationHistory(db.Model):
    __tablename__ = 'channel_validation_history'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    channel_config_id = db.Column(db.BigInteger, nullable=False, index=True)
    validation_type = db.Column(db.String(50), nullable=False)  # setup, permission_check, periodic
    validation_result = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text, default=None)
    permissions_snapshot = db.Column(db.JSON, default=None)  # JSONB in PostgreSQL
    validated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'channel_config_id': self.channel_config_id,
            'validation_type': self.validation_type,
            'validation_result': self.validation_result,
            'error_message': self.error_message,
            'permissions_snapshot': self.permissions_snapshot,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None
        }
    
    @classmethod
    def create_validation_record(cls, channel_config_id, validation_type, result, error_message=None, permissions=None):
        """Create a new validation history record"""
        record = cls(
            channel_config_id=channel_config_id,
            validation_type=validation_type,
            validation_result=result,
            error_message=error_message,
            permissions_snapshot=permissions
        )
        return record
    
    def __repr__(self):
        return f'<ChannelValidationHistory {self.validation_type} for config {self.channel_config_id}: {self.validation_result}>'

