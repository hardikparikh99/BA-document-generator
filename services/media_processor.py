"""
Media processing service for the CrewAI Multi-Agent Project Documentation System.
This module handles audio extraction and transcription using FFmpeg and Whisper.
"""
import os
import subprocess
import tempfile
import asyncio
from typing import Dict, Any, Optional, List
import whisper
import ffmpeg
from pydub import AudioSegment

from utils.config import get_settings
from utils.logger import setup_logger
from utils.file_handler import is_video_file, is_audio_file

# Setup logger
logger = setup_logger(__name__)
settings = get_settings()

class MediaProcessor:
    """
    Service for processing media files (audio/video) and generating transcriptions.
    """
    
    def __init__(self):
        """Initialize the media processor."""
        self.whisper_model = None
        self.whisper_model_name = "base"  # Options: tiny, base, small, medium, large
        self.initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the Whisper model.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if self.initialized:
            return True
            
        try:
            # Load Whisper model
            logger.info(f"Loading Whisper model: {self.whisper_model_name}")
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            self.initialized = True
            logger.info("Media processor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing media processor: {str(e)}")
            return False
    
    async def extract_audio_from_video(self, video_path: str) -> Dict[str, Any]:
        """
        Extract audio from a video file using FFmpeg.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            dict: Result of the operation with success status and audio_path
        """
        try:
            # Create temporary file for audio output
            audio_path = os.path.join(
                os.path.dirname(video_path),
                f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.wav"
            )
            
            # Run FFmpeg to extract audio
            logger.info(f"Extracting audio from video: {video_path}")
            
            # Use ffmpeg-python to extract audio
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ar=16000)
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.info(f"Audio extracted successfully: {audio_path}")
            return {
                "success": True,
                "audio_path": audio_path
            }
        except Exception as e:
            logger.error(f"Error extracting audio from video: {str(e)}")
            return {
                "success": False,
                "message": f"Error extracting audio: {str(e)}"
            }
    
    async def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            dict: Result of the operation with success status, transcription, and metadata
        """
        # Initialize if not already
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return {
                    "success": False,
                    "message": "Failed to initialize Whisper model"
                }
        
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Get audio duration with proper file handling
            try:
                audio = AudioSegment.from_file(audio_path)
                duration_seconds = len(audio) / 1000  # Convert milliseconds to seconds
                # Explicitly delete the audio object to release file handles
                del audio
            except Exception as e:
                logger.warning(f"Error getting audio duration: {str(e)}")
                duration_seconds = 0  # Default value if we can't get the duration
            
            # Run transcription in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.whisper_model.transcribe(audio_path)
            )
            
            transcription = result["text"]
            language = result["language"]
            
            logger.info(f"Transcription completed successfully: {len(transcription)} characters")
            
            # Extract metadata
            metadata = {
                "duration": duration_seconds,
                "language": language,
                "file_type": os.path.splitext(audio_path)[1][1:],  # Remove the dot
                "speakers": None  # Whisper doesn't do speaker diarization by default
            }
            
            return {
                "success": True,
                "transcription": transcription,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {
                "success": False,
                "message": f"Error transcribing audio: {str(e)}"
            }
    
    async def process_media_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a media file (audio or video) and generate a transcription.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            dict: Result of the operation with success status, transcription, and metadata
        """
        try:
            # Determine file type
            if is_video_file(file_path):
                logger.info(f"Processing video file: {file_path}")
                
                # Extract audio from video
                extract_result = await self.extract_audio_from_video(file_path)
                if not extract_result["success"]:
                    return extract_result
                
                audio_path = extract_result["audio_path"]
                
                # Transcribe the extracted audio
                transcribe_result = await self.transcribe_audio(audio_path)
                
                # Clean up temporary audio file
                try:
                    os.remove(audio_path)
                except Exception as e:
                    logger.warning(f"Error removing temporary audio file: {str(e)}")
                
                return transcribe_result
                
            elif is_audio_file(file_path):
                logger.info(f"Processing audio file: {file_path}")
                
                # Transcribe audio directly
                return await self.transcribe_audio(file_path)
                
            else:
                logger.error(f"Unsupported file type: {file_path}")
                return {
                    "success": False,
                    "message": "Unsupported file type"
                }
                
        except Exception as e:
            logger.error(f"Error processing media file: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing media file: {str(e)}"
            }
    
    async def check_ffmpeg_availability(self) -> bool:
        """
        Check if FFmpeg is available on the system.
        
        Returns:
            bool: True if FFmpeg is available, False otherwise
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
