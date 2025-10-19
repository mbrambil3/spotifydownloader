import { useState } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { Download, Music, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [playlistUrl, setPlaylistUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [playlist, setPlaylist] = useState(null);
  const [downloadingTrack, setDownloadingTrack] = useState(null);
  const [downloadingAll, setDownloadingAll] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleLoadPlaylist = async () => {
    if (!playlistUrl.trim()) {
      toast.error("Por favor, insira uma URL válida");
      return;
    }

    setLoading(true);
    setPlaylist(null);
    setProgress(0);

    try {
      const response = await axios.post(`${API}/playlist`, {
        url: playlistUrl
      });
      setPlaylist(response.data);
      toast.success("Playlist carregada com sucesso!");
    } catch (error) {
      console.error("Error loading playlist:", error);
      const message = error.response?.data?.detail || "Erro ao carregar playlist. Verifique se a URL está correta e a playlist é pública.";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTrack = async (track) => {
    setDownloadingTrack(track.id);
    
    try {
      const response = await axios.post(
        `${API}/download-track`,
        {
          track_name: track.name,
          track_artist: track.artist,
          track_id: track.id
        },
        {
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${track.name} - ${track.artist}.mp3`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`${track.name} baixada com sucesso!`);
    } catch (error) {
      console.error("Error downloading track:", error);
      
      // Parse error message from backend
      let errorMessage = "Erro ao baixar música. Tente novamente.";
      if (error.response?.data) {
        try {
          const errorText = await error.response.data.text();
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch (e) {
          // If can't parse, use default message
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setDownloadingTrack(null);
    }
  };

  const handleDownloadAll = async () => {
    if (!playlist || playlist.tracks.length === 0) {
      toast.error("Nenhuma música disponível");
      return;
    }

    setDownloadingAll(true);
    setProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 1000);

      const response = await axios.post(
        `${API}/download-all`,
        {
          playlist_id: playlist.id,
          tracks: playlist.tracks
        },
        {
          responseType: 'blob'
        }
      );

      clearInterval(progressInterval);
      setProgress(100);

      // Check download summary from headers
      const summary = response.headers['x-download-summary'];
      const failedTracks = response.headers['x-failed-tracks'];

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${playlist.name}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      // Show appropriate message
      if (summary) {
        const [success, total] = summary.split('/').map(Number);
        if (success === total) {
          toast.success(`Todas as ${total} músicas baixadas com sucesso!`);
        } else {
          toast.warning(`${success} de ${total} músicas baixadas. Algumas podem estar indisponíveis no YouTube.`);
        }
      } else {
        toast.success("Download concluído!");
      }
    } catch (error) {
      console.error("Error downloading all:", error);
      
      // Parse error message from backend
      let errorMessage = "Erro ao baixar playlist completa. Tente novamente.";
      if (error.response?.data) {
        try {
          const errorText = await error.response.data.text();
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch (e) {
          // If can't parse, use default message
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setDownloadingAll(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const formatDuration = (ms) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${seconds.padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12 pt-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-emerald-500/10 p-4 rounded-2xl backdrop-blur-sm border border-emerald-500/20">
              <Music className="w-12 h-12 text-emerald-400" />
            </div>
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold mb-4 bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
            SpotiDown
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Baixe suas playlists favoritas do Spotify de forma rápida e simples
          </p>
        </div>

        {/* Input Section */}
        <Card className="bg-slate-900/50 backdrop-blur-sm border-slate-800 mb-8" data-testid="playlist-input-card">
          <CardHeader>
            <CardTitle className="text-slate-100">Cole o link da playlist</CardTitle>
            <CardDescription className="text-slate-400">
              Insira a URL da playlist pública do Spotify
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-3">
              <Input
                data-testid="playlist-url-input"
                type="text"
                placeholder="https://open.spotify.com/playlist/..."
                value={playlistUrl}
                onChange={(e) => setPlaylistUrl(e.target.value)}
                className="flex-1 bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-emerald-500"
                onKeyPress={(e) => e.key === 'Enter' && handleLoadPlaylist()}
              />
              <Button
                data-testid="load-playlist-button"
                onClick={handleLoadPlaylist}
                disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-8"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Carregando...
                  </>
                ) : (
                  "Carregar"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Playlist Info */}
        {playlist && (
          <div className="space-y-6" data-testid="playlist-content">
            <Card className="bg-slate-900/50 backdrop-blur-sm border-slate-800">
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row gap-6 items-start">
                  {playlist.image_url && (
                    <img
                      src={playlist.image_url}
                      alt={playlist.name}
                      className="w-32 h-32 rounded-xl shadow-2xl object-cover"
                      data-testid="playlist-image"
                    />
                  )}
                  <div className="flex-1">
                    <h2 className="text-3xl font-bold text-slate-100 mb-2" data-testid="playlist-name">
                      {playlist.name}
                    </h2>
                    {playlist.description && (
                      <p className="text-slate-400 mb-4" data-testid="playlist-description">
                        {playlist.description.replace(/<[^>]*>/g, '')}
                      </p>
                    )}
                    <p className="text-slate-500 mb-4" data-testid="playlist-track-count">
                      {playlist.total_tracks} {playlist.total_tracks === 1 ? 'música' : 'músicas'}
                    </p>
                    <Button
                      data-testid="download-all-button"
                      onClick={handleDownloadAll}
                      disabled={downloadingAll}
                      className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold"
                    >
                      {downloadingAll ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Baixando {playlist.total_tracks} músicas...
                        </>
                      ) : (
                        <>
                          <Download className="w-4 h-4 mr-2" />
                          Baixar todas ({playlist.total_tracks})
                        </>
                      )}
                    </Button>
                    {downloadingAll && progress > 0 && (
                      <div className="mt-4" data-testid="download-progress">
                        <Progress value={progress} className="h-2" />
                        <p className="text-sm text-slate-400 mt-2">{progress}% completo</p>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tracks List */}
            <div className="space-y-3">
              {playlist.tracks.map((track, index) => (
                <Card
                  key={track.id}
                  className="bg-slate-900/30 backdrop-blur-sm border-slate-800 hover:bg-slate-900/50 hover:border-slate-700 transition-all duration-200"
                  data-testid={`track-card-${index}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      <div className="text-slate-500 font-medium w-8 text-center">
                        {index + 1}
                      </div>
                      {track.image_url && (
                        <img
                          src={track.image_url}
                          alt={track.album}
                          className="w-14 h-14 rounded-lg object-cover shadow-lg"
                          data-testid={`track-image-${index}`}
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-slate-100 font-semibold truncate" data-testid={`track-name-${index}`}>
                          {track.name}
                        </h3>
                        <p className="text-slate-400 text-sm truncate" data-testid={`track-artist-${index}`}>
                          {track.artist}
                        </p>
                      </div>
                      <div className="text-slate-500 text-sm hidden sm:block">
                        {formatDuration(track.duration_ms)}
                      </div>
                      <Button
                        data-testid={`download-track-button-${index}`}
                        size="sm"
                        onClick={() => handleDownloadTrack(track)}
                        disabled={downloadingTrack === track.id}
                        className="bg-slate-800 hover:bg-emerald-600 text-slate-100 hover:text-white transition-colors"
                      >
                        {downloadingTrack === track.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Download className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!playlist && !loading && (
          <div className="text-center py-16" data-testid="empty-state">
            <div className="bg-slate-900/30 backdrop-blur-sm border border-slate-800 rounded-2xl p-12 max-w-md mx-auto">
              <AlertCircle className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 text-lg">
                Nenhuma playlist carregada ainda
              </p>
              <p className="text-slate-500 text-sm mt-2">
                Cole o link de uma playlist do Spotify acima
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;