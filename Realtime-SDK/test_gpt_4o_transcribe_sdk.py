import pytest
import asyncio
import os
import json
import base64
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Import the module under test
import sys
sys.path.append(os.path.dirname(__file__))
import gpt_4o_transcribe_sdk
from gpt_4o_transcribe_sdk import RealtimeTranscriberSDK, DEPLOYMENT_NAME


class TestRealtimeTranscriberSDK:
    """Test suite for the Azure OpenAI SDK-based realtime transcriber."""
    
    @pytest.fixture
    def transcriber(self):
        """Create a transcriber instance for testing."""
        with patch('pyaudio.PyAudio'):
            return RealtimeTranscriberSDK()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock websocket for testing."""
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=None)
        return mock_ws
    
    def test_initialization(self, transcriber):
        """Test that the transcriber initializes correctly."""
        assert transcriber.audio_interface is not None
        assert transcriber.stream is None
        assert transcriber.is_streaming is False
        assert transcriber.websocket is None
    
    @patch('pyaudio.PyAudio.open')
    def test_setup_audio_stream(self, mock_open, transcriber):
        """Test audio stream setup."""
        mock_stream = Mock()
        mock_open.return_value = mock_stream
        
        transcriber.setup_audio_stream()
        
        assert transcriber.stream == mock_stream
        mock_open.assert_called_once()
    
    def test_cleanup(self, transcriber):
        """Test cleanup of resources."""
        # Setup mock objects
        mock_stream = Mock()
        mock_audio_interface = Mock()
        transcriber.stream = mock_stream
        transcriber.audio_interface = mock_audio_interface
        transcriber.is_streaming = True
        
        transcriber.cleanup()
        
        assert transcriber.is_streaming is False
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_audio_interface.terminate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_session_config(self, transcriber, mock_websocket):
        """Test sending session configuration."""
        transcriber.websocket = mock_websocket
        
        await transcriber.send_session_config()
        
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        config = json.loads(call_args)
        
        assert config["type"] == "transcription_session.update"
        assert config["session"]["input_audio_format"] == "pcm16"
        assert config["session"]["input_audio_transcription"]["model"] == DEPLOYMENT_NAME
        assert config["session"]["input_audio_transcription"]["language"] == "en"
    
    @pytest.mark.asyncio
    async def test_stream_microphone(self, transcriber, mock_websocket):
        """Test microphone streaming functionality."""
        transcriber.websocket = mock_websocket
        transcriber.is_streaming = True
        
        # Mock audio stream
        mock_stream = Mock()
        mock_stream.read.return_value = b'\x00' * 1024  # Mock audio data
        transcriber.stream = mock_stream
        
        # Create a task that will run briefly and then stop
        async def stop_after_delay():
            await asyncio.sleep(0.1)
            transcriber.is_streaming = False
        
        # Run both tasks concurrently
        stop_task = asyncio.create_task(stop_after_delay())
        stream_task = asyncio.create_task(transcriber.stream_microphone())
        
        await asyncio.gather(stop_task, stream_task, return_exceptions=True)
        
        # Verify that audio data was sent
        assert mock_websocket.send.called
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "input_audio_buffer.append"
        assert "audio" in message
    
    @pytest.mark.asyncio
    async def test_handle_websocket_messages_transcription_delta(self, transcriber, capsys):
        """Test handling of transcription delta messages."""
        transcriber.websocket = Mock()
        
        # Mock the async iteration
        async def mock_messages():
            yield json.dumps({
                "type": "conversation.item.input_audio_transcription.delta",
                "delta": "Hello "
            })
            yield json.dumps({
                "type": "conversation.item.input_audio_transcription.delta", 
                "delta": "world"
            })
        
        transcriber.websocket.__aiter__ = lambda: mock_messages()
        
        # Run the handler with a timeout to prevent infinite loop
        try:
            await asyncio.wait_for(transcriber.handle_websocket_messages(), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        
        captured = capsys.readouterr()
        assert "Hello " in captured.out
        assert "world" in captured.out
    
    @pytest.mark.asyncio
    async def test_handle_websocket_messages_transcription_completed(self, transcriber, capsys):
        """Test handling of completed transcription messages."""
        transcriber.websocket = Mock()
        
        # Mock the async iteration
        async def mock_messages():
            yield json.dumps({
                "type": "conversation.item.input_audio_transcription.completed",
                "transcript": "Hello world, this is a test."
            })
        
        transcriber.websocket.__aiter__ = lambda: mock_messages()
        
        # Run the handler with a timeout
        try:
            await asyncio.wait_for(transcriber.handle_websocket_messages(), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        
        captured = capsys.readouterr()
        assert "Hello world, this is a test." in captured.out
    
    @pytest.mark.asyncio
    async def test_handle_websocket_messages_error(self, transcriber, capsys):
        """Test handling of error messages."""
        transcriber.websocket = Mock()
        
        # Mock the async iteration
        async def mock_messages():
            yield json.dumps({
                "type": "error",
                "error": {"message": "Test error"}
            })
        
        transcriber.websocket.__aiter__ = lambda: mock_messages()
        
        # Run the handler with a timeout
        try:
            await asyncio.wait_for(transcriber.handle_websocket_messages(), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        
        captured = capsys.readouterr()
        assert "Error event:" in captured.out
    
    @pytest.mark.asyncio
    async def test_handle_websocket_malformed_json(self, transcriber, capsys):
        """Test handling of malformed JSON messages."""
        transcriber.websocket = Mock()
        
        # Mock the async iteration
        async def mock_messages():
            yield "invalid json {"
            yield json.dumps({"type": "valid_message"})
        
        transcriber.websocket.__aiter__ = lambda: mock_messages()
        
        # Run the handler with a timeout
        try:
            await asyncio.wait_for(transcriber.handle_websocket_messages(), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        
        captured = capsys.readouterr()
        assert "Event type: valid_message" in captured.out
    
    @pytest.mark.asyncio
    @patch('websockets.connect')
    @patch('gpt_4o_transcribe_sdk.client')
    async def test_connect_and_run(self, mock_client, mock_connect, transcriber):
        """Test the main connection and run logic."""
        # Setup mocks
        mock_client.api_key = "test_key"
        mock_client._version = "1.0.0"
        
        mock_websocket = AsyncMock()
        mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
        mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the async iteration to prevent infinite loop
        mock_websocket.__aiter__ = lambda: asyncio.iter([])
        
        # Mock stream setup
        transcriber.stream = Mock()
        transcriber.stream.read.return_value = b'\x00' * 1024
        
        # Run with timeout to prevent hanging
        try:
            await asyncio.wait_for(transcriber.connect_and_run(), timeout=0.5)
        except asyncio.TimeoutError:
            pass
        
        # Verify connection was attempted
        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args[1]
        assert "extra_headers" in call_kwargs
        assert call_kwargs["extra_headers"]["api-key"] == "test_key"


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Test that missing API key raises error."""
        with pytest.raises(RuntimeError, match="AZURE_OPENAI_STT_TTS_KEY is missing"):
            # Reload the module to trigger the environment check
            import importlib
            import sys
            if 'gpt_4o_transcribe_sdk' in sys.modules:
                importlib.reload(sys.modules['gpt_4o_transcribe_sdk'])
    
    @patch.dict(os.environ, {"AZURE_OPENAI_STT_TTS_KEY": "test_key"}, clear=True)
    def test_missing_endpoint(self):
        """Test that missing endpoint raises error."""
        with pytest.raises(RuntimeError, match="AZURE_OPENAI_STT_TTS_ENDPOINT is missing"):
            # Reload the module to trigger the environment check
            import importlib
            import sys
            if 'gpt_4o_transcribe_sdk' in sys.modules:
                importlib.reload(sys.modules['gpt_4o_transcribe_sdk'])


class TestIntegration:
    """Integration tests for the full functionality."""
    
    @pytest.mark.asyncio
    @patch('websockets.connect')
    @patch('pyaudio.PyAudio')
    async def test_full_run_with_mocks(self, mock_pyaudio, mock_connect, capsys):
        """Test a full run of the transcriber with mocked dependencies."""
        # Setup environment
        with patch.dict(os.environ, {
            "AZURE_OPENAI_STT_TTS_KEY": "test_key",
            "AZURE_OPENAI_STT_TTS_ENDPOINT": "https://test.openai.azure.com"
        }):
            # Setup mocks
            mock_audio_interface = Mock()
            mock_stream = Mock()
            mock_stream.read.return_value = b'\x00' * 1024
            mock_audio_interface.open.return_value = mock_stream
            mock_pyaudio.return_value = mock_audio_interface
            
            mock_websocket = AsyncMock()
            mock_websocket.send = AsyncMock()
            
            # Mock websocket messages
            async def mock_messages():
                yield json.dumps({
                    "type": "conversation.item.input_audio_transcription.completed",
                    "transcript": "Test transcription"
                })
            
            mock_websocket.__aiter__ = lambda: mock_messages()
            mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
            mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Import and run
            from gpt_4o_transcribe_sdk import RealtimeTranscriberSDK
            transcriber = RealtimeTranscriberSDK()
            
            # Run with timeout
            try:
                await asyncio.wait_for(transcriber.run(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            
            # Verify output
            captured = capsys.readouterr()
            assert "Connecting to Azure OpenAI Realtime API..." in captured.out


if __name__ == "__main__":
    pytest.main([__file__])