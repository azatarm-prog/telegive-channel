import pytest
from unittest.mock import patch, Mock
import requests
from utils.telegram_api import (
    get_channel_info,
    get_bot_member_info,
    validate_channel_setup,
    get_bot_info
)

class TestTelegramChannelIntegration:
    
    @patch('requests.get')
    def test_get_channel_info_success(self, mock_get):
        """Test successful channel info retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'id': -1001234567890,
                'title': 'Test Channel',
                'username': 'testchannel',
                'type': 'channel',
                'members_count': 1000
            }
        }
        mock_get.return_value = mock_response
        
        result = get_channel_info('bot_token', '@testchannel')
        
        assert result['success'] == True
        assert result['channel_info']['id'] == -1001234567890
        assert result['channel_info']['title'] == 'Test Channel'
        assert result['channel_info']['username'] == 'testchannel'
        assert result['channel_info']['members_count'] == 1000
    
    @patch('requests.get')
    def test_get_channel_info_not_found(self, mock_get):
        """Test channel not found scenario"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        
        result = get_channel_info('bot_token', '@nonexistent')
        
        assert result['success'] == False
        assert 'not found' in result['error'].lower() or 'not accessible' in result['error'].lower()
    
    @patch('requests.get')
    def test_get_channel_info_api_error(self, mock_get):
        """Test Telegram API error response"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Chat not found'
        }
        mock_get.return_value = mock_response
        
        result = get_channel_info('bot_token', '@testchannel')
        
        assert result['success'] == False
        assert result['error'] == 'Chat not found'
    
    @patch('requests.get')
    def test_get_channel_info_timeout(self, mock_get):
        """Test channel info request timeout"""
        mock_get.side_effect = requests.Timeout()
        
        result = get_channel_info('bot_token', '@testchannel')
        
        assert result['success'] == False
        assert 'timeout' in result['error'].lower()
    
    @patch('requests.get')
    def test_get_channel_info_network_error(self, mock_get):
        """Test network error during channel info request"""
        mock_get.side_effect = requests.RequestException('Network error')
        
        result = get_channel_info('bot_token', '@testchannel')
        
        assert result['success'] == False
        assert 'network error' in result['error'].lower()
    
    def test_get_channel_info_username_formatting(self):
        """Test channel username formatting"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {
                'ok': True,
                'result': {
                    'id': -1001234567890,
                    'title': 'Test Channel',
                    'type': 'channel'
                }
            }
            mock_get.return_value = mock_response
            
            # Test with @ prefix
            result = get_channel_info('bot_token', '@testchannel')
            assert result['success'] == True
            
            # Test without @ prefix
            result = get_channel_info('bot_token', 'testchannel')
            assert result['success'] == True
            
            # Verify the API was called with @ prefix in both cases
            calls = mock_get.call_args_list
            for call in calls:
                params = call[1]['params']
                assert params['chat_id'].startswith('@')
    
    @patch('requests.get')
    def test_get_bot_member_info_success(self, mock_get):
        """Test successful bot member info retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'status': 'administrator',
                'can_post_messages': True,
                'can_edit_messages': True,
                'can_send_media_messages': True,
                'can_delete_messages': False,
                'can_pin_messages': False
            }
        }
        mock_get.return_value = mock_response
        
        result = get_bot_member_info('bot_token', -1001234567890, 1234567890)
        
        assert result['success'] == True
        assert result['member_info']['status'] == 'administrator'
        assert result['member_info']['can_post_messages'] == True
        assert result['member_info']['can_edit_messages'] == True
        assert result['member_info']['can_send_media_messages'] == True
    
    @patch('requests.get')
    def test_get_bot_member_info_not_member(self, mock_get):
        """Test bot not member scenario"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Bad Request: user not found'
        }
        mock_get.return_value = mock_response
        
        result = get_bot_member_info('bot_token', -1001234567890, 1234567890)
        
        assert result['success'] == False
        assert 'user not found' in result['error'].lower()
    
    @patch('requests.get')
    def test_get_bot_member_info_timeout(self, mock_get):
        """Test bot member info request timeout"""
        mock_get.side_effect = requests.Timeout()
        
        result = get_bot_member_info('bot_token', -1001234567890, 1234567890)
        
        assert result['success'] == False
        assert 'timeout' in result['error'].lower()
    
    @patch('utils.telegram_api.get_channel_info')
    @patch('utils.telegram_api.get_bot_member_info')
    def test_validate_channel_setup_success(self, mock_member_info, mock_channel_info):
        """Test successful complete channel setup validation"""
        mock_channel_info.return_value = {
            'success': True,
            'channel_info': {
                'id': -1001234567890,
                'title': 'Test Channel',
                'username': 'testchannel',
                'type': 'channel',
                'members_count': 1000
            }
        }
        
        mock_member_info.return_value = {
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
        
        result = validate_channel_setup('bot_token', 1234567890, 'testchannel')
        
        assert result['success'] == True
        assert 'channel_info' in result
        assert 'permissions' in result
        assert result['channel_info']['id'] == -1001234567890
        assert result['permissions']['can_post_messages'] == True
    
    @patch('utils.telegram_api.get_channel_info')
    def test_validate_channel_setup_channel_not_found(self, mock_channel_info):
        """Test channel setup validation when channel not found"""
        mock_channel_info.return_value = {
            'success': False,
            'error': 'Chat not found'
        }
        
        result = validate_channel_setup('bot_token', 1234567890, 'nonexistent')
        
        assert result['success'] == False
        assert result['error'] == 'Chat not found'
    
    @patch('utils.telegram_api.get_channel_info')
    @patch('utils.telegram_api.get_bot_member_info')
    def test_validate_channel_setup_not_admin(self, mock_member_info, mock_channel_info):
        """Test channel setup validation when bot is not admin"""
        mock_channel_info.return_value = {
            'success': True,
            'channel_info': {
                'id': -1001234567890,
                'title': 'Test Channel'
            }
        }
        
        mock_member_info.return_value = {
            'success': True,
            'member_info': {
                'status': 'member',
                'can_post_messages': False
            }
        }
        
        result = validate_channel_setup('bot_token', 1234567890, 'testchannel')
        
        assert result['success'] == False
        assert 'not an administrator' in result['error']
    
    @patch('utils.telegram_api.get_channel_info')
    @patch('utils.telegram_api.get_bot_member_info')
    def test_validate_channel_setup_missing_permissions(self, mock_member_info, mock_channel_info):
        """Test channel setup validation with missing permissions"""
        mock_channel_info.return_value = {
            'success': True,
            'channel_info': {
                'id': -1001234567890,
                'title': 'Test Channel'
            }
        }
        
        mock_member_info.return_value = {
            'success': True,
            'member_info': {
                'status': 'administrator',
                'can_post_messages': False,  # Missing required permission
                'can_edit_messages': True,
                'can_send_media_messages': True
            }
        }
        
        result = validate_channel_setup('bot_token', 1234567890, 'testchannel')
        
        assert result['success'] == False
        assert 'lacks required permissions' in result['error']
        assert 'can_post_messages' in result['error']
    
    @patch('utils.telegram_api.get_channel_info')
    @patch('utils.telegram_api.get_bot_member_info')
    def test_validate_channel_setup_member_info_error(self, mock_member_info, mock_channel_info):
        """Test channel setup validation when member info fails"""
        mock_channel_info.return_value = {
            'success': True,
            'channel_info': {
                'id': -1001234567890,
                'title': 'Test Channel'
            }
        }
        
        mock_member_info.return_value = {
            'success': False,
            'error': 'User not found in chat'
        }
        
        result = validate_channel_setup('bot_token', 1234567890, 'testchannel')
        
        assert result['success'] == False
        assert result['error'] == 'User not found in chat'
    
    @patch('requests.get')
    def test_get_bot_info_success(self, mock_get):
        """Test successful bot info retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'id': 1234567890,
                'username': 'test_bot',
                'first_name': 'Test Bot',
                'is_bot': True
            }
        }
        mock_get.return_value = mock_response
        
        result = get_bot_info('bot_token')
        
        assert result['success'] == True
        assert result['bot_info']['id'] == 1234567890
        assert result['bot_info']['username'] == 'test_bot'
        assert result['bot_info']['is_bot'] == True
    
    @patch('requests.get')
    def test_get_bot_info_invalid_token(self, mock_get):
        """Test bot info with invalid token"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = get_bot_info('invalid_token')
        
        assert result['success'] == False
        assert 'invalid bot token' in result['error'].lower()
    
    @patch('requests.get')
    def test_get_bot_info_api_error(self, mock_get):
        """Test bot info with API error"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Unauthorized'
        }
        mock_get.return_value = mock_response
        
        result = get_bot_info('bot_token')
        
        assert result['success'] == False
        assert result['error'] == 'Unauthorized'
    
    @patch('requests.get')
    def test_get_bot_info_timeout(self, mock_get):
        """Test bot info request timeout"""
        mock_get.side_effect = requests.Timeout()
        
        result = get_bot_info('bot_token')
        
        assert result['success'] == False
        assert 'timeout' in result['error'].lower()

class TestTelegramAPIErrorHandling:
    
    @patch('requests.get')
    def test_unexpected_response_format(self, mock_get):
        """Test handling of unexpected response format"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'unexpected': 'format'
        }
        mock_get.return_value = mock_response
        
        result = get_channel_info('bot_token', '@testchannel')
        
        assert result['success'] == False
        assert 'error' in result
    
    @patch('requests.get')
    def test_json_decode_error(self, mock_get):
        """Test handling of JSON decode error"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_get.return_value = mock_response
        
        result = get_channel_info('bot_token', '@testchannel')
        
        assert result['success'] == False
        assert 'error' in result
    
    @patch('requests.get')
    def test_connection_error(self, mock_get):
        """Test handling of connection error"""
        mock_get.side_effect = requests.ConnectionError('Connection failed')
        
        result = get_channel_info('bot_token', '@testchannel')
        
        assert result['success'] == False
        assert 'network error' in result['error'].lower()
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters"""
        # Test with None values
        result = get_channel_info(None, '@testchannel')
        assert result['success'] == False
        
        result = get_channel_info('bot_token', None)
        assert result['success'] == False
        
        result = get_bot_member_info('bot_token', None, 123)
        assert result['success'] == False
        
        result = get_bot_member_info('bot_token', -123, None)
        assert result['success'] == False

