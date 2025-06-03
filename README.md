# Realtime TTS with Azure OpenAI GPT-4o Mini Transcribe

This repository explores the new GPT-4o mini Transcribe model from Azure OpenAI, implementing a simple real-time speech transcription application. The project is inspired by the blog post:  
[Real-time speech transcription with GPT-4o Transcribe and GPT-4o Mini Transcribe](https://techcommunity.microsoft.com/blog/azure-ai-services-blog/real-time-speech-transcription-with-gpt-4o-transcribe-and-gpt-4o-mini-transcribe/4410353)

## Goals

1. Experiment with the GPT-4o mini Transcribe model via Azure OpenAI.
2. Build a working application based on the guidance from the referenced blog.

## Implementation Notes & Challenges

While following the blog, a few implementation details required adjustment:

- **Query String Parameter Difference:**  
  The OpenAI API for transcription uses a `intent` query string parameter. Using this same parameter with an Azure OpenAI endpoint caused WebSocket connection issues.

- **Switch to `deployment` Parameter:**  
  Following Azure OpenAI Realtime API guidance, changing the query string parameter from `intent` to `deployment` resolved the connection issues.

- **Event Type Differences:**  
  After updating the URI, the event types sent by the server changed. Instead of receiving `conversation` objects as described in the blog, the API began sending `response` objects.

## Summary

This repository demonstrates how to adapt the blog's approach for use with Azure OpenAI, highlighting subtle but important differences in API usage and event handling.

## References

- [Azure AI Services Blog: Real-time speech transcription with GPT-4o Transcribe and GPT-4o Mini Transcribe](https://techcommunity.microsoft.com/blog/azure-ai-services-blog/real-time-speech-transcription-with-gpt-4o-transcribe-and-gpt-4o-mini-transcribe/4410353)
- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
