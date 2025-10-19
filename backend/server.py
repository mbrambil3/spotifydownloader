from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import asyncio
import zipfile
import shutil
from concurrent.futures import ThreadPoolExecutor
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Spotify client
spotify_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
    client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET')
))

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Thread pool for async execution
executor = ThreadPoolExecutor(max_workers=4)

# Download directory
DOWNLOAD_DIR = Path("/tmp/spotify_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Models
class PlaylistRequest(BaseModel):
    url: str

class Track(BaseModel):
    id: str
    name: str
    artist: str
    album: str
    image_url: Optional[str] = None
    duration_ms: int

class PlaylistResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    total_tracks: int
    tracks: List[Track]

class DownloadRequest(BaseModel):
    track_name: str
    track_artist: str
    track_id: str

class DownloadAllRequest(BaseModel):
    playlist_id: str
    tracks: List[Track]

def extract_playlist_id(url: str) -> str:
    """Extract Spotify playlist ID from URL"""
    patterns = [
        r'playlist/([a-zA-Z0-9]+)',
        r'playlist:([a-zA-Z0-9]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Invalid Spotify playlist URL")

def download_from_youtube(query: str, output_path: Path) -> bool:
    """Download audio from YouTube and convert to MP3"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_path / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'default_search': 'ytsearch1:',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
        return True
    except Exception as e:
        logging.error(f"Download error: {e}")
        return False

@api_router.get("/")
async def root():
    return {"message": "Spotify Playlist Downloader API"}

@api_router.post("/playlist", response_model=PlaylistResponse)
async def get_playlist(request: PlaylistRequest):
    """Get playlist information from Spotify"""
    try:
        # Extract playlist ID
        playlist_id = extract_playlist_id(request.url)
        
        # Get playlist from Spotify with market parameter
        playlist = spotify_client.playlist(playlist_id, market='BR')
        
        # Extract tracks
        tracks = []
        for item in playlist['tracks']['items']:
            if item['track'] and item['track']['id']:  # Check if track exists and has ID
                track = item['track']
                tracks.append(Track(
                    id=track['id'],
                    name=track['name'],
                    artist=', '.join([artist['name'] for artist in track['artists']]),
                    album=track['album']['name'],
                    image_url=track['album']['images'][0]['url'] if track['album']['images'] else None,
                    duration_ms=track['duration_ms']
                ))
        
        if not tracks:
            raise HTTPException(status_code=400, detail="Esta playlist está vazia ou não possui músicas disponíveis.")
        
        return PlaylistResponse(
            id=playlist['id'],
            name=playlist['name'],
            description=playlist.get('description'),
            image_url=playlist['images'][0]['url'] if playlist['images'] else None,
            total_tracks=len(tracks),
            tracks=tracks
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error fetching playlist: {error_msg}")
        
        # Check for specific error types
        if '404' in error_msg:
            raise HTTPException(
                status_code=404, 
                detail="Playlist não encontrada. Verifique se a URL está correta e se a playlist é pública. Nota: algumas playlists geradas pelo Spotify podem ter restrições regionais."
            )
        elif '401' in error_msg or '403' in error_msg:
            raise HTTPException(status_code=403, detail="Acesso negado. A playlist pode ser privada.")
        else:
            raise HTTPException(status_code=500, detail="Erro ao buscar playlist. Tente novamente.")

@api_router.post("/download-track")
async def download_track(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Download a single track"""
    try:
        # Create unique directory for this download
        download_id = str(uuid.uuid4())
        track_dir = DOWNLOAD_DIR / download_id
        track_dir.mkdir(exist_ok=True)
        
        # Search query
        query = f"{request.track_name} {request.track_artist}"
        
        # Download in background
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            executor,
            download_from_youtube,
            query,
            track_dir
        )
        
        if not success:
            # Cleanup
            try:
                shutil.rmtree(track_dir)
            except:
                pass
            raise HTTPException(
                status_code=404, 
                detail=f"Não foi possível encontrar/baixar '{request.track_name}' no YouTube. A música pode estar bloqueada ou indisponível."
            )
        
        # Find the downloaded file
        mp3_files = list(track_dir.glob("*.mp3"))
        if not mp3_files:
            # Cleanup
            try:
                shutil.rmtree(track_dir)
            except:
                pass
            raise HTTPException(
                status_code=404, 
                detail=f"Arquivo não encontrado após download. A música '{request.track_name}' pode não estar disponível."
            )
        
        file_path = mp3_files[0]
        
        # Schedule cleanup
        def cleanup():
            try:
                shutil.rmtree(track_dir)
            except:
                pass
        
        background_tasks.add_task(cleanup)
        
        return FileResponse(
            path=file_path,
            filename=f"{request.track_name} - {request.track_artist}.mp3",
            media_type="audio/mpeg"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading track: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar download")

@api_router.post("/download-all")
async def download_all(request: DownloadAllRequest, background_tasks: BackgroundTasks):
    """Download all tracks and create a ZIP file"""
    try:
        # Create unique directory for this download
        download_id = str(uuid.uuid4())
        zip_dir = DOWNLOAD_DIR / download_id
        zip_dir.mkdir(exist_ok=True)
        
        loop = asyncio.get_event_loop()
        
        # Download all tracks
        for track in request.tracks:
            query = f"{track.name} {track.artist}"
            await loop.run_in_executor(
                executor,
                download_from_youtube,
                query,
                zip_dir
            )
        
        # Create ZIP file
        zip_path = DOWNLOAD_DIR / f"{download_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for mp3_file in zip_dir.glob("*.mp3"):
                zipf.write(mp3_file, mp3_file.name)
        
        # Schedule cleanup
        def cleanup():
            try:
                shutil.rmtree(zip_dir)
                if zip_path.exists():
                    zip_path.unlink()
            except:
                pass
        
        background_tasks.add_task(cleanup)
        
        return FileResponse(
            path=zip_path,
            filename=f"{request.playlist_id}_playlist.zip",
            media_type="application/zip"
        )
    
    except Exception as e:
        logging.error(f"Error downloading all tracks: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar download em lote")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()