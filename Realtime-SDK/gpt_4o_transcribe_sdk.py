import os
import json
import base64
import threading
import asyncio
import pyaudio
import websockets
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv('.env')  # Load environment variables from .env

# Azure OpenAI configuration
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_STT_TTS_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_STT_TTS_ENDPOINT")
DEPLOYMENT_NAME = "gpt-4o-mini-transcribe"

if not AZURE_OPENAI_API_KEY:
    raise RuntimeError("❌ AZURE_OPENAI_STT_TTS_KEY is missing!")
if not AZURE_OPENAI_ENDPOINT:
    raise RuntimeError("❌ AZURE_OPENAI_STT_TTS_ENDPOINT is missing!")

# Initialize Azure OpenAI client for SDK operations
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2025-04-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# WebSocket URL for realtime API (since SDK doesn't directly support realtime WebSocket yet)
websocket_url = f"{AZURE_OPENAI_ENDPOINT.replace('https', 'wss')}/openai/realtime?api-version=2025-04-01-preview&deployment={DEPLOYMENT_NAME}"
headers = {"api-key": AZURE_OPENAI_API_KEY}

# Audio stream parameters (16-bit PCM, 24kHz mono)
RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024

class RealtimeTranscriberSDK:
    """
    Azure OpenAI Realtime Transcriber using SDK patterns and WebSocket connection.
    
    This implementation uses the Azure OpenAI SDK for authentication and configuration
    while leveraging WebSocket for the realtime connection, following Microsoft Learn
    guidance for Azure OpenAI integration.
    """
    
    def __init__(self):
        self.audio_interface = pyaudio.PyAudio()
        self.stream = None
        self.is_streaming = False
        self.websocket = None
        
    def setup_audio_stream(self):
        """Setup PyAudio stream for microphone input."""
        self.stream = self.audio_interface.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
    def cleanup(self):
        """Cleanup audio resources."""
        self.is_streaming = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio_interface:
            self.audio_interface.terminate()
            
    async def send_session_config(self):
        """Send initial session configuration to the realtime API."""
        session_config = {
            "type": "transcription_session.update",
            "session": {
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": DEPLOYMENT_NAME,
                    "prompt": "Respond in English.",
                    "language": "en",
                },
                "input_audio_noise_reduction": {"type": "near_field"},
                "turn_detection": {
                    "type": "server_vad", 
                    "threshold": 0.5, 
                    "prefix_padding_ms": 300, 
                    "silence_duration_ms": 200
                }
            }
        }
        await self.websocket.send(json.dumps(session_config))
        
    async def stream_microphone(self):
        """Stream microphone audio to the realtime session."""
        try:
            while self.is_streaming and self.websocket:
                audio_data = self.stream.read(CHUNK, exception_on_overflow=False)
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                message = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64,
                }
                
                await self.websocket.send(json.dumps(message))
                
        except Exception as e:
            print("Audio streaming error:", e)
            self.is_streaming = False
            
    async def handle_websocket_messages(self):
        """Handle messages from the WebSocket connection."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    event_type = data.get("type", "")
                    print("Event type:", event_type)
                    
                    # Handle transcription delta events
                    if event_type == "conversation.item.input_audio_transcription.delta":
                        transcript_piece = data.get("delta", "")
                        if transcript_piece:
                            print(transcript_piece, end=' ', flush=True)
                            
                    # Handle completed transcriptions
                    elif event_type == "conversation.item.input_audio_transcription.completed":
                        transcript = data.get("transcript", "")
                        if transcript:
                            print(f"\n{transcript}")
                            
                    # Handle response text deltas
                    elif event_type == "response.text.delta":
                        delta_text = data.get("delta", "")
                        if delta_text:
                            print(f"📥: {delta_text}")
                            
                    # Handle response text completion
                    elif event_type == "response.text.done":
                        final_text = data.get("text", "")
                        if final_text:
                            print("📨:", final_text)
                            
                    # Handle item events
                    elif event_type == "item":
                        transcript = data.get("item", "")
                        if transcript:
                            print("\nFinal transcript:", transcript)
                            
                    # Handle errors
                    elif event_type == "error":
                        print("Error event:", data)
                        
                except json.JSONDecodeError:
                    # Ignore malformed JSON messages
                    pass
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        except Exception as e:
            print(f"Error handling WebSocket messages: {e}")
            
    async def connect_and_run(self):
        """Connect to the realtime API and start processing."""
        try:
            print("Connecting to Azure OpenAI Realtime API...")
            
            # Use SDK client's configuration for authentication
            extra_headers = {
                "api-key": client.api_key,
                "User-Agent": f"openai-python-sdk/{client._version}"
            }
            
            async with websockets.connect(
                websocket_url,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                self.websocket = websocket
                self.is_streaming = True
                
                print("Connected! Start speaking...")
                
                # Send initial session configuration
                await self.send_session_config()
                
                # Start audio streaming task
                audio_task = asyncio.create_task(self.stream_microphone())
                
                # Start message handling task
                message_task = asyncio.create_task(self.handle_websocket_messages())
                
                # Wait for either task to complete (or fail)
                try:
                    await asyncio.gather(audio_task, message_task)
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.cleanup()
            
    async def run(self):
        """Main method to run the transcriber."""
        try:
            self.setup_audio_stream()
            await self.connect_and_run()
        except KeyboardInterrupt:
            print("Interrupted by user. Closing...")
        finally:
            self.cleanup()

async def main():
    """Main function to run the application."""
    transcriber = RealtimeTranscriberSDK()
    await transcriber.run()

if __name__ == "__main__":
    asyncio.run(main())