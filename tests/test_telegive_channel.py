import pytest
import requests
from unittest.mock import patch, Mock
from app import create_app
from models import db, ChannelConfig, ChannelValidationHistory
from config.settings import config

class TestChannelService:
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def sample_channel_config(self, app):
        """Create sample channel configuration"""
        with app.app_context():
            config = ChannelConfig(
                account_id=1,
                channel_id=-1001234567890,
                channel_username='testchannel',
                channel_title='Test Channel',
                channel_type='channel',
                channel_member_count=1000,
                can_post_messages=True,
                can_edit_messages=True,
                can_send_media_messages=True,
                can_delete_messages=False,
                can_pin_messages=False,
                is_validated=True
            )
            db.session.add(config)
            db.session.commit()
            yield config
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert 'service' in data
        assert 'version' in data
        assert data['service'] == 'channel-service'
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'service' in data
        assert 'version' in data
        assert 'status' in data
        assert 'endpoints' in data
    
    @patch('utils.telegram_api.validate_channel_setup')
    def test_setup_channel_success(self, mock_validate, client):
        """Test successful channel setup"""
        mock_validate.return_value = {
            'success': True,
            'channel_info': {
                'id': -1001234567890,
                'title': 'Test Channel',
                'username': 'testchannel',
                'type': 'channel',
                'members_count': 1000
            },
            'permissions': {
                'can_post_messages': True,
                'can_edit_messages': True,
                'can_send_media_messages': True,
                'can_delete_messages': False,
                'can_pin_messages': False
            }
        }
        
        response = client.post('/api/channels/setup', json={
            'account_id': 1,
            'channel_username': 'testchannel'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'channel_info' in data
        assert 'permissions' in data
    
    @patch('utils.telegram_api.validate_channel_setup')
    def test_setup_channel_not_admin(self, mock_validate, client):
        """Test channel setup when bot is not admin"""
        mock_validate.return_value = {
            'success': False,
            'error': 'Bot is not an administrator in the channel'
        }
        
        response = client.post('/api/channels/setup', json={
            'account_id': 1,
            'channel_username': 'testchannel'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
        assert 'not an administrator' in data['error']
    
    @patch('utils.telegram_api.validate_channel_setup')
    def test_setup_channel_missing_permissions(self, mock_validate, client):
        """Test channel setup with missing permissions"""
        mock_validate.return_value = {
            'success': False,
            'error': 'Bot lacks required permissions: can_post_messages'
        }
        
        response = client.post('/api/channels/setup', json={
            'account_id': 1,
            'channel_username': 'testchannel'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
        assert 'lacks required permissions' in data['error']
    
    def test_setup_channel_missing_data(self, client):
        """Test channel setup with missing data"""
        response = client.post('/api/channels/setup', json={})
        assert response.status_code == 400
        
        response = client.post('/api/channels/setup', json={
            'account_id': 1
        })
        assert response.status_code == 400
        
        response = client.post('/api/channels/setup', json={
            'channel_username': 'testchannel'
        })
        assert response.status_code == 400
    
    def test_validate_existing_channel(self, client, sample_channel_config):
        """Test validation of existing channel configuration"""
        with patch('utils.telegram_api.get_bot_member_info') as mock_member:
            mock_member.return_value = {
                'success': True,
                'member_info': {
                    'status': 'administrator',
                    'can_post_messages': True,
                    'can_edit_messages': True,
                    'can_send_media_messages': True,
                    'can_delete_messages': False,
                    'can_pin_messages': False
                }
            }
            
            response = client.get('/api/channels/validate/1')
            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] == True
            assert 'channel_info' in data
    
    def test_validate_nonexistent_channel(self, client):
        """Test validation of nonexistent channel"""
        response = client.get('/api/channels/validate/999')
        assert response.status_code == 404
        data = response.get_json()
        assert data['valid'] == False
        assert 'not found' in data['error'].lower()
    
    def test_get_channel_permissions(self, client, sample_channel_config):
        """Test getting channel permissions"""
        response = client.get('/api/channels/permissions/1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'permissions' in data
        assert data['permissions']['can_post_messages'] == True
        assert data['permissions']['can_send_media_messages'] == True
    
    def test_get_channel_permissions_not_found(self, client):
        """Test getting permissions for nonexistent channel"""
        response = client.get('/api/channels/permissions/999')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] == False
    
    def test_update_permissions(self, client, sample_channel_config):
        """Test updating channel permissions"""
        new_permissions = {
            'can_post_messages': True,
            'can_edit_messages': True,
            'can_send_media_messages': False,
            'can_delete_messages': True,
            'can_pin_messages': True
        }
        
        response = client.put('/api/channels/update-permissions', json={
            'account_id': 1,
            'permissions': new_permissions
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['updated_permissions']['can_send_media_messages'] == False
        assert data['updated_permissions']['can_delete_messages'] == True
    
    def test_update_permissions_with_error(self, client, sample_channel_config):
        """Test updating permissions with validation error"""
        new_permissions = {
            'can_post_messages': False,
            'can_edit_messages': True,
            'can_send_media_messages': True
        }
        
        response = client.put('/api/channels/update-permissions', json={
            'account_id': 1,
            'permissions': new_permissions,
            'validation_error': 'Permission denied for posting messages'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
    
    def test_get_channel_info(self, client, sample_channel_config):
        """Test getting complete channel information"""
        response = client.get('/api/channels/info/1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'channel' in data
        assert data['channel']['username'] == 'testchannel'
        assert data['channel']['title'] == 'Test Channel'
        assert data['channel']['member_count'] == 1000
    
    def test_get_channel_info_not_found(self, client):
        """Test getting info for nonexistent channel"""
        response = client.get('/api/channels/info/999')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] == False
    
    @patch('utils.telegram_api.get_bot_member_info')
    @patch('utils.telegram_api.get_channel_info')
    def test_revalidate_channel(self, mock_channel_info, mock_member_info, client, sample_channel_config):
        """Test channel revalidation"""
        mock_member_info.return_value = {
            'success': True,
            'member_info': {
                'status': 'administrator',
                'can_post_messages': True,
                'can_edit_messages': True,
                'can_send_media_messages': True
            }
        }
        
        mock_channel_info.return_value = {
            'success': True,
            'channel_info': {
                'title': 'Updated Test Channel',
                'members_count': 1100
            }
        }
        
        response = client.post('/api/channels/revalidate/1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'validation_result' in data
    
    def test_revalidate_nonexistent_channel(self, client):
        """Test revalidation of nonexistent channel"""
        response = client.post('/api/channels/revalidate/999')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] == False
    
    def test_get_channel_status(self, client, sample_channel_config):
        """Test getting comprehensive channel status"""
        response = client.get('/api/channels/status/1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'status' in data
    
    def test_list_channels(self, client, sample_channel_config):
        """Test listing all channels"""
        response = client.get('/api/channels/list')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'channels' in data
        assert data['total'] == 1
        assert data['channels'][0]['channel_username'] == 'testchannel'
    
    def test_list_channels_empty(self, client):
        """Test listing channels when none exist"""
        response = client.get('/api/channels/list')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['total'] == 0
        assert len(data['channels']) == 0

class TestChannelConfigModel:
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        app = create_app('testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    def test_channel_config_creation(self, app):
        """Test creating a channel configuration"""
        with app.app_context():
            db.create_all()
            
            config = ChannelConfig(
                account_id=1,
                channel_id=-1001234567890,
                channel_username='testchannel',
                channel_title='Test Channel',
                can_post_messages=True,
                can_edit_messages=True,
                can_send_media_messages=True
            )
            
            db.session.add(config)
            db.session.commit()
            
            assert config.id is not None
            assert config.account_id == 1
            assert config.channel_username == 'testchannel'
            assert config.is_validated == False  # Default value
    
    def test_channel_config_to_dict(self, app):
        """Test converting channel config to dictionary"""
        with app.app_context():
            db.create_all()
            
            config = ChannelConfig(
                account_id=1,
                channel_id=-1001234567890,
                channel_username='testchannel',
                channel_title='Test Channel'
            )
            
            config_dict = config.to_dict()
            assert 'id' in config_dict
            assert 'account_id' in config_dict
            assert 'permissions' in config_dict
            assert config_dict['channel_username'] == 'testchannel'
    
    def test_channel_config_permissions(self, app):
        """Test channel config permission methods"""
        with app.app_context():
            db.create_all()
            
            config = ChannelConfig(
                account_id=1,
                channel_id=-1001234567890,
                channel_username='testchannel',
                channel_title='Test Channel',
                can_post_messages=True,
                can_edit_messages=False
            )
            
            permissions = config.get_permissions_dict()
            assert permissions['can_post_messages'] == True
            assert permissions['can_edit_messages'] == False
            
            # Update permissions
            new_permissions = {
                'can_post_messages': False,
                'can_edit_messages': True,
                'can_send_media_messages': True
            }
            
            config.update_permissions(new_permissions)
            
            updated_permissions = config.get_permissions_dict()
            assert updated_permissions['can_post_messages'] == False
            assert updated_permissions['can_edit_messages'] == True
            assert updated_permissions['can_send_media_messages'] == True

class TestValidationHistoryModel:
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        app = create_app('testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    def test_validation_history_creation(self, app):
        """Test creating validation history record"""
        with app.app_context():
            db.create_all()
            
            # Create channel config first
            config = ChannelConfig(
                account_id=1,
                channel_id=-1001234567890,
                channel_username='testchannel',
                channel_title='Test Channel'
            )
            db.session.add(config)
            db.session.commit()
            
            # Create validation history
            history = ChannelValidationHistory.create_validation_record(
                channel_config_id=config.id,
                validation_type='setup',
                result=True,
                permissions={'can_post_messages': True}
            )
            
            db.session.add(history)
            db.session.commit()
            
            assert history.id is not None
            assert history.channel_config_id == config.id
            assert history.validation_type == 'setup'
            assert history.validation_result == True
    
    def test_validation_history_to_dict(self, app):
        """Test converting validation history to dictionary"""
        with app.app_context():
            db.create_all()
            
            history = ChannelValidationHistory(
                channel_config_id=1,
                validation_type='permission_check',
                validation_result=False,
                error_message='Test error'
            )
            
            history_dict = history.to_dict()
            assert 'id' in history_dict
            assert 'validation_type' in history_dict
            assert history_dict['validation_result'] == False
            assert history_dict['error_message'] == 'Test error'

