"""
Media Processing Agent for the CrewAI Multi-Agent Project Documentation System.
This agent handles audio extraction from video and transcription using Whisper.
"""
import os
from typing import Dict, Any, Optional, List
import asyncio

from crewai import Agent, Task
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from utils.config import get_settings
from utils.logger import get_agent_logger
from utils.file_handler import is_video_file, is_audio_file
from services.media_processor import MediaProcessor
from models.database import update_processing_status

# Setup logger
logger = get_agent_logger("media_processing")
settings = get_settings()

class FFmpegTool(BaseTool):
    """Tool for extracting audio from video using FFmpeg."""
    
    name: str = "ffmpeg_tool"
    description: str = "Extracts audio from video files"
    
    def __init__(self):
        """Initialize the FFmpeg tool."""
        super().__init__()
        # Initialize MediaProcessor lazily to avoid potential circular imports
        self._media_processor = None
    
    @property
    def media_processor(self):
        """Lazy initialization of MediaProcessor."""
        if self._media_processor is None:
            self._media_processor = MediaProcessor()
        return self._media_processor
    
    async def _arun(self, video_path: str) -> Dict[str, Any]:
        """
        Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            dict: Result of the operation with audio_path
        """
        try:
            # Ensure the video path exists
            if not os.path.exists(video_path):
                return {
                    "success": False,
                    "message": f"Video file not found: {video_path}"
                }
                
            # Extract audio using MediaProcessor
            result = await self.media_processor.extract_audio_from_video(video_path)
            return result
        except Exception as e:
            logger.error(f"Error in FFmpegTool: {str(e)}")
            return {
                "success": False,
                "message": f"Error extracting audio: {str(e)}"
            }
    
    def _run(self, video_path: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(video_path))

class WhisperTool(BaseTool):
    """Tool for transcribing audio using Whisper."""
    
    name: str = "whisper_tool"
    description: str = "Transcribes audio files using Whisper"
    
    def __init__(self):
        """Initialize the Whisper tool."""
        super().__init__()
        # Initialize MediaProcessor lazily to avoid potential circular imports
        self._media_processor = None
    
    @property
    def media_processor(self):
        """Lazy initialization of MediaProcessor."""
        if self._media_processor is None:
            self._media_processor = MediaProcessor()
        return self._media_processor
    
    async def _arun(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            dict: Result of the operation with transcription and metadata
        """
        try:
            # Ensure the audio path exists
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "message": f"Audio file not found: {audio_path}"
                }
                
            # Transcribe audio using MediaProcessor
            result = await self.media_processor.transcribe_audio(audio_path)
            return result
        except Exception as e:
            logger.error(f"Error in WhisperTool: {str(e)}")
            return {
                "success": False,
                "message": f"Error transcribing audio: {str(e)}"
            }
    
    def _run(self, audio_path: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(audio_path))

class AudioProcessingTool(BaseTool):
    """Tool for processing audio files."""
    
    name: str = "audio_processing_tool"
    description: str = "Processes audio files for better transcription quality"
    
    def __init__(self):
        """Initialize the audio processing tool."""
        super().__init__()
        # Initialize MediaProcessor lazily to avoid potential circular imports
        self._media_processor = None
    
    @property
    def media_processor(self):
        """Lazy initialization of MediaProcessor."""
        if self._media_processor is None:
            self._media_processor = MediaProcessor()
        return self._media_processor
    
    async def _arun(self, audio_path: str) -> Dict[str, Any]:
        """
        Process an audio file for better transcription quality.
        This is a placeholder for more advanced audio processing.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            dict: Result of the operation with processed_audio_path
        """
        try:
            # Ensure the audio path exists
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "message": f"Audio file not found: {audio_path}"
                }
                
            # This is a placeholder for more advanced audio processing
            # In a real implementation, this could include noise reduction,
            # normalization, etc.
            
            # For now, we'll just return the original audio path
            # In a real implementation, we would process the audio and return a new path
            return {
                "success": True,
                "processed_audio_path": audio_path,
                "message": "Audio processing completed successfully"
            }
        except Exception as e:
            logger.error(f"Error in AudioProcessingTool: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing audio: {str(e)}"
            }
    
    def _run(self, audio_path: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(audio_path))

class MediaProcessingAgent:
    """
    Agent responsible for processing media files and generating transcriptions.
    """
    
    def __init__(self):
        """Initialize the Media Processing Agent."""
        self.logger = logger
        
        # Create tools
        self.ffmpeg_tool = FFmpegTool()
        self.whisper_tool = WhisperTool()
        self.audio_processing_tool = AudioProcessingTool()
        
        # Create CrewAI agent
        self.agent = Agent(
            role="Media Processing Specialist",
            goal="Convert video to audio and generate transcriptions",
            backstory="Expert in multimedia processing and speech recognition",
            verbose=True,
            tools=[]
        )
        
        # Add tools to agent after initialization
        self.agent.tools = [self.ffmpeg_tool, self.whisper_tool, self.audio_processing_tool]
    
    async def process_file(self, file_id: str, file_path: str) -> Dict[str, Any]:
        """
        Process a media file and generate a transcription.
        
        Args:
            file_id: Unique identifier for the file
            file_path: Path to the file
            
        Returns:
            dict: Result of the operation with transcription and metadata
        """
        try:
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=25,
                current_stage="extraction"
            )
            
            # Check if file exists
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                self.logger.error(error_msg)
                
                await update_processing_status(
                    file_id=file_id,
                    status="failed",
                    progress=0,
                    current_stage="extraction",
                    error=error_msg
                )
                
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Step 1: Extract audio if it's a video file
            if is_video_file(file_path):
                self.logger.info(f"Extracting audio from video: {file_path}")
                
                # Use FFmpegTool to extract audio
                extract_result = await self.ffmpeg_tool._arun(file_path)
                
                if not extract_result.get("success", False):
                    error_msg = extract_result.get("message", "Failed to extract audio from video")
                    self.logger.error(f"Audio extraction failed: {error_msg}")
                    
                    await update_processing_status(
                        file_id=file_id,
                        status="failed",
                        progress=25,
                        current_stage="extraction",
                        error=error_msg
                    )
                    
                    return {
                        "success": False,
                        "message": error_msg
                    }
                
                audio_path = extract_result["audio_path"]
                self.logger.info(f"Audio extracted successfully: {audio_path}")
            else:
                # It's already an audio file
                audio_path = file_path
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=40,
                current_stage="audio_processing"
            )
            
            # Step 2: Process audio for better quality (optional)
            process_result = await self.audio_processing_tool._arun(audio_path)
            
            if not process_result.get("success", False):
                error_msg = process_result.get("message", "Failed to process audio")
                self.logger.error(f"Audio processing failed: {error_msg}")
                
                await update_processing_status(
                    file_id=file_id,
                    status="failed",
                    progress=40,
                    current_stage="audio_processing",
                    error=error_msg
                )
                
                return {
                    "success": False,
                    "message": error_msg
                }
            
            processed_audio_path = process_result["processed_audio_path"]
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=50,
                current_stage="transcription"
            )
            
            # Step 3: Transcribe audio
            self.logger.info(f"Transcribing audio: {processed_audio_path}")
            transcribe_result = await self.whisper_tool._arun(processed_audio_path)
            
            if not transcribe_result.get("success", False):
                error_msg = transcribe_result.get("message", "Failed to transcribe audio")
                self.logger.error(f"Transcription failed: {error_msg}")
                
                await update_processing_status(
                    file_id=file_id,
                    status="failed",
                    progress=50,
                    current_stage="transcription",
                    error=error_msg
                )
                
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Clean up temporary files if needed
            if is_video_file(file_path) and audio_path != file_path:
                # Wait a moment to ensure file handles are released
                await asyncio.sleep(1)
                
                # Try multiple times to remove the file
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                            self.logger.info(f"Removed temporary audio file: {audio_path}")
                            break
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            self.logger.warning(f"Attempt {attempt+1}/{max_attempts}: Could not remove temporary file: {str(e)}")
                            # Wait longer between attempts
                            await asyncio.sleep(2)
                        else:
                            self.logger.warning(f"Failed to remove temporary audio file after {max_attempts} attempts: {str(e)}")
                            # Schedule removal for later
                            asyncio.create_task(self._schedule_file_cleanup(audio_path))
            
            # Force garbage collection to release file handles
            import gc
            gc.collect()
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="completed",
                progress=60,
                current_stage="transcription_completed"
            )
            
            return {
                "success": True,
                "transcription": transcribe_result["transcription"],
                "metadata": transcribe_result["metadata"]
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error in process_file: {error_msg}")
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=0,
                current_stage="error",
                error=error_msg
            )
            
            return {
                "success": False,
                "message": f"Error processing file: {error_msg}"
            }
    
    async def _schedule_file_cleanup(self, file_path: str, delay_seconds: int = 30):
        """
        Schedule a file for cleanup after a specified delay.
        
        Args:
            file_path: Path to the file to clean up
            delay_seconds: Number of seconds to wait before attempting cleanup
        """
        try:
            # Wait for the specified delay
            await asyncio.sleep(delay_seconds)
            
            # Check if file still exists and try to remove it
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Successfully removed delayed cleanup file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Error in delayed file cleanup for {file_path}: {str(e)}")
    
    def create_task(self, file_id: str, file_path: str) -> Task:
        """
        Create a CrewAI task for media processing.
        
        Args:
            file_id: Unique identifier for the file
            file_path: Path to the file
            
        Returns:
            Task: CrewAI task
        """
        return Task(
            description=f"Process media file {file_id} at {file_path} and generate transcription",
            agent=self.agent,
            expected_output="Transcription text and metadata"
        )
