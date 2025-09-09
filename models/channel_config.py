from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class ChannelConfig(db.Model):
    __tablename__ = 'channel_configs'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    account_id = db.Column(db.BigInteger, nullable=False, index=True)
    channel_id = db.Column(db.BigInteger, nullable=False, index=True)
    channel_username = db.Column(db.String(100), nullable=False)
    channel_title = db.Column(db.String(255), nullable=False)
    channel_type = db.Column(db.String(20), default='channel')  # channel, supergroup
    channel_member_count = db.Column(db.Integer, default=0)
    
    # Bot permissions in channel
    can_post_messages = db.Column(db.Boolean, default=False)
    can_edit_messages = db.Column(db.Boolean, default=False)
    can_send_media_messages = db.Column(db.Boolean, default=False)
    can_delete_messages = db.Column(db.Boolean, default=False)
    can_pin_messages = db.Column(db.Boolean, default=False)
    
    # Validation status
    is_validated = db.Column(db.Boolean, default=False)
    last_validation_at = db.Column(db.DateTime(timezone=True), default=None)
    validation_error = db.Column(db.Text, default=None)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one channel per account
    __table_args__ = (
        db.UniqueConstraint('account_id', name='uq_channel_configs_account_id'),
    )
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'channel_id': self.channel_id,
            'channel_username': self.channel_username,
            'channel_title': self.channel_title,
            'channel_type': self.channel_type,
            'channel_member_count': self.channel_member_count,
            'permissions': {
                'can_post_messages': self.can_post_messages,
                'can_edit_messages': self.can_edit_messages,
                'can_send_media_messages': self.can_send_media_messages,
                'can_delete_messages': self.can_delete_messages,
                'can_pin_messages': self.can_pin_messages
            },
            'is_validated': self.is_validated,
            'last_validation_at': self.last_validation_at.isoformat() if self.last_validation_at else None,
            'validation_error': self.validation_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_permissions_dict(self):
        """Get permissions as dictionary"""
        return {
            'can_post_messages': self.can_post_messages,
            'can_edit_messages': self.can_edit_messages,
            'can_send_media_messages': self.can_send_media_messages,
            'can_delete_messages': self.can_delete_messages,
            'can_pin_messages': self.can_pin_messages
        }
    
    def update_permissions(self, permissions_dict):
        """Update permissions from dictionary"""
        for permission, value in permissions_dict.items():
            if hasattr(self, permission):
                setattr(self, permission, value)
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<ChannelConfig {self.channel_username} for account {self.account_id}>'

