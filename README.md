# Realtime TTS with Azure OpenAI GPT-4o Mini Transcribe

This repository explores the new GPT-4o mini Transcribe model from Azure OpenAI, implementing real-time speech transcription applications. The project is inspired by the blog post:  
[Real-time speech transcription with GPT-4o Transcribe and GPT-4o Mini Transcribe](https://techcommunity.microsoft.com/blog/azure-ai-services-blog/real-time-speech-transcription-with-gpt-4o-transcribe-and-gpt-4o-mini-transcribe/4410353)

## Implementations

This repository now contains two implementations of the same functionality:

### 1. Original WebSocket Implementation (`gpt-4o-transcribe-websocket.py`)
The original implementation using direct WebSocket connections with the `websocket-client` library.

### 2. Azure SDK Implementation (`Realtime-SDK/`)
A modern implementation leveraging the Azure OpenAI SDK with async/await patterns, following [Microsoft Learn guidance](https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-quickstart?tabs=keyless%2Cmacos&pivots=programming-language-python).

Key features of the SDK implementation:
- Uses Azure OpenAI SDK for authentication and configuration
- Async/await architecture for better performance
- Comprehensive test suite
- Enhanced error handling and resource management
- Detailed documentation

## Goals

1. Experiment with the GPT-4o mini Transcribe model via Azure OpenAI.
2. Build working applications based on the guidance from the referenced blog.
3. Demonstrate both direct WebSocket and SDK-based approaches.
4. Provide comprehensive testing and documentation.

## Quick Start

### Original Implementation
```bash
pip install -r requirements.txt
python gpt-4o-transcribe-websocket.py
```

### SDK Implementation
```bash
cd Realtime-SDK
pip install -r requirements.txt
python gpt_4o_transcribe_sdk.py
```

Both implementations require the same environment variables:
```bash
AZURE_OPENAI_STT_TTS_KEY=your_azure_openai_api_key
AZURE_OPENAI_STT_TTS_ENDPOINT=https://your-resource.openai.azure.com
```

## Implementation Notes & Challenges

While following the blog, a few implementation details required adjustment:

- **Query String Parameter Difference:**  
  The OpenAI API for transcription uses a `intent` query string parameter. Using this same parameter with an Azure OpenAI endpoint caused WebSocket connection issues.

- **Switch to `deployment` Parameter:**  
  Following Azure OpenAI Realtime API guidance, changing the query string parameter from `intent` to `deployment` resolved the connection issues.

- **Event Type Differences:**  
  After updating the URI, the event types sent by the server changed. Instead of receiving `conversation` objects as described in the blog, the API began sending `response` objects.

## Architecture Comparison

| Feature | Original (websocket-client) | SDK Implementation |
|---------|---------------------------|-------------------|
| Library | websocket-client | openai + websockets |
| Architecture | Synchronous + threading | Asynchronous |
| Authentication | Manual headers | SDK-managed |
| Error Handling | Basic | Comprehensive |
| Testing | None | Full test suite |
| Documentation | Minimal | Extensive |

## Testing

The SDK implementation includes a comprehensive test suite:

```bash
cd Realtime-SDK
python -m pytest test_gpt_4o_transcribe_sdk.py -v
```

## Summary

This repository demonstrates how to adapt the blog's approach for use with Azure OpenAI, highlighting subtle but important differences in API usage and event handling. It provides both a simple WebSocket implementation and a more robust SDK-based approach with modern Python patterns.

## References

- [Azure AI Services Blog: Real-time speech transcription with GPT-4o Transcribe and GPT-4o Mini Transcribe](https://techcommunity.microsoft.com/blog/azure-ai-services-blog/real-time-speech-transcription-with-gpt-4o-transcribe-and-gpt-4o-mini-transcribe/4410353)
- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure OpenAI Realtime Audio Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-quickstart?tabs=keyless%2Cmacos&pivots=programming-language-python)
