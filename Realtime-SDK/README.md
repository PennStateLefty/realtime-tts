# Azure OpenAI Realtime Transcription - SDK Implementation

This directory contains a second implementation of the realtime speech transcription application using the Azure OpenAI SDK patterns and modern async/await architecture.

## Overview

This implementation follows the guidance from the [Microsoft Learn article on Azure OpenAI Realtime Audio](https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-quickstart?tabs=keyless%2Cmacos&pivots=programming-language-python) and demonstrates how to integrate the Azure OpenAI SDK with realtime WebSocket connections.

## Key Features

- **Azure OpenAI SDK Integration**: Uses the official Azure OpenAI SDK for authentication and configuration
- **Async/Await Architecture**: Modern asynchronous programming patterns for better performance
- **WebSocket Connection**: Direct WebSocket connection for realtime audio streaming
- **Comprehensive Error Handling**: Robust error handling and cleanup
- **Modular Design**: Clean class-based architecture for maintainability

## Differences from Original Implementation

While maintaining the same core functionality as the original `gpt-4o-transcribe-websocket.py`, this implementation offers several improvements:

1. **SDK-based Authentication**: Leverages the Azure OpenAI SDK for proper authentication and configuration
2. **Async Architecture**: Uses asyncio for concurrent audio streaming and message handling
3. **Better Resource Management**: Improved cleanup and resource management
4. **Enhanced Documentation**: Comprehensive docstrings and comments
5. **Testability**: Modular design that supports comprehensive unit testing

## Requirements

See `requirements.txt` for dependencies:
- `openai>=1.55.0` - Azure OpenAI SDK
- `python-dotenv` - Environment variable management
- `pyaudio` - Audio capture and processing
- `websockets` - WebSocket client for realtime connection

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:
```
AZURE_OPENAI_STT_TTS_KEY=your_azure_openai_api_key
AZURE_OPENAI_STT_TTS_ENDPOINT=https://your-resource.openai.azure.com
```

## Usage

Run the SDK-based transcriber:

```bash
python gpt-4o-transcribe-sdk.py
```

The application will:
1. Connect to Azure OpenAI Realtime API using SDK authentication
2. Start capturing audio from your microphone
3. Stream audio data to the API for real-time transcription
4. Display transcription results as they arrive

## Architecture

### RealtimeTranscriberSDK Class

The main class that orchestrates the transcription process:

- `setup_audio_stream()`: Configures PyAudio for microphone capture
- `connect_and_run()`: Establishes WebSocket connection using SDK authentication
- `stream_microphone()`: Async audio streaming to the API
- `handle_websocket_messages()`: Processes realtime transcription events
- `cleanup()`: Proper resource cleanup

### Key Methods

- **Authentication**: Uses Azure OpenAI SDK client for proper API key management
- **Session Configuration**: Sends initial configuration for transcription parameters
- **Event Handling**: Processes various event types (deltas, completions, errors)
- **Concurrent Processing**: Handles audio streaming and message processing concurrently

## Event Types Handled

The implementation handles the same event types as the original:

- `conversation.item.input_audio_transcription.delta` - Streaming transcription pieces
- `conversation.item.input_audio_transcription.completed` - Complete transcriptions
- `response.text.delta` - Response text streaming
- `response.text.done` - Complete response text
- `error` - Error events

## Testing

Run the comprehensive test suite:

```bash
python -m pytest test_gpt_4o_transcribe_sdk.py -v
```

The test suite includes:
- Unit tests for all major components
- Mock-based testing for external dependencies
- Integration tests for full workflow
- Error handling and edge case testing

## Error Handling

The implementation includes robust error handling for:
- Network connection issues
- Audio capture problems
- WebSocket communication errors
- Malformed JSON messages
- Resource cleanup on interruption

## Configuration

The implementation uses the same environment variables as the original:
- `AZURE_OPENAI_STT_TTS_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_STT_TTS_ENDPOINT`: Your Azure OpenAI endpoint URL

## Comparison with Original

| Feature | Original (websocket-client) | SDK Implementation |
|---------|---------------------------|-------------------|
| Authentication | Manual header setup | SDK-managed authentication |
| Architecture | Synchronous with threading | Asynchronous with asyncio |
| WebSocket Library | websocket-client | websockets |
| Error Handling | Basic | Comprehensive |
| Testing | None | Full test suite |
| Documentation | Minimal | Extensive |
| Resource Management | Manual | Automatic cleanup |

## Future Enhancements

Potential improvements for future versions:
- Native SDK realtime support (when available)
- Additional audio format support
- Configurable transcription parameters
- Integration with other Azure services
- Performance optimizations