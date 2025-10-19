# SpotiDown - Documentação Completa do Projeto

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Funcionalidades](#funcionalidades)
3. [Tecnologias e Ferramentas](#tecnologias-e-ferramentas)
4. [Arquitetura do Sistema](#arquitetura-do-sistema)
5. [Alterações Detalhadas](#alterações-detalhadas)
6. [Como Funciona](#como-funciona)
7. [Limitações e Observações](#limitações-e-observações)

---

## 🎯 Visão Geral

**SpotiDown** é uma aplicação web funcional, moderna e rápida que permite aos usuários baixar playlists do Spotify de forma simples, prática e segura.

### O Que Faz?
- Extrai informações de playlists públicas do Spotify via API oficial
- Busca e baixa as músicas correspondentes do YouTube
- Converte automaticamente para formato MP3
- Oferece download individual ou em lote (arquivo ZIP)

### Propósito
Facilitar o acesso offline às músicas de playlists do Spotify, permitindo que usuários baixem suas playlists favoritas em formato MP3.

---

## ✨ Funcionalidades

### 1. **Carregamento de Playlist**
- Input para URL da playlist do Spotify
- Validação automática da URL
- Suporte a playlists públicas e criadas por usuários
- Extração de metadados completos via Spotify Web API

### 2. **Visualização de Dados**
- **Informações da Playlist:**
  - Capa da playlist
  - Nome e descrição
  - Número total de músicas
  
- **Lista de Músicas:**
  - Número sequencial
  - Capa do álbum
  - Nome da música
  - Nome do artista
  - Duração formatada (mm:ss)

### 3. **Download Individual**
- Botão de download para cada música
- Busca automática no YouTube baseada em metadados
- Conversão para MP3 (192 kbps)
- Feedback visual durante o processo
- Tratamento de erros específico

### 4. **Download em Lote**
- Botão "Baixar todas" para download completo
- Criação automática de arquivo ZIP
- Barra de progresso visual
- Continua o processo mesmo se algumas músicas falharem
- Resumo de downloads (ex: "9 de 13 músicas baixadas")

### 5. **Interface e UX**
- Design responsivo (mobile e desktop)
- Modo escuro (dark mode)
- Notificações toast para feedback
- Mensagens de erro amigáveis e específicas
- Animações suaves
- Estados de loading claros

---

## 🛠 Tecnologias e Ferramentas

### Backend (FastAPI)

#### Frameworks e Bibliotecas
```python
fastapi==0.110.1          # Framework web moderno e rápido
uvicorn==0.25.0           # Servidor ASGI
motor==3.3.1              # Driver MongoDB assíncrono
pydantic>=2.6.4           # Validação de dados
python-dotenv>=1.0.1      # Gerenciamento de variáveis de ambiente
```

#### Integrações Principais
```python
spotipy==2.25.1           # Cliente Python para Spotify Web API
yt-dlp==2025.10.14        # Download e conversão de vídeos do YouTube
```

#### Ferramentas Auxiliares
- **FFmpeg**: Conversão de áudio para MP3
- **zipfile**: Criação de arquivos ZIP
- **ThreadPoolExecutor**: Processamento assíncrono de downloads

### Frontend (React)

#### Framework Base
```json
"react": "^19.0.0"
"react-dom": "^19.0.0"
"react-scripts": "5.0.1"
```

#### Bibliotecas UI
```json
"@radix-ui/*": "Componentes UI modernos e acessíveis"
"lucide-react": "^0.507.0"     // Ícones
"sonner": "^2.0.3"              // Sistema de toasts
"tailwindcss": "^3.4.17"        // Estilização
```

#### Utilitários
```json
"axios": "^1.8.4"              // Cliente HTTP
"react-router-dom": "^7.5.1"   // Roteamento
"class-variance-authority": "^0.7.1"  // Gerenciamento de classes CSS
```

### Banco de Dados
- **MongoDB**: Armazenamento (estrutura pronta, não utilizado na aplicação principal)

### Infraestrutura
- **Supervisor**: Gerenciamento de processos
- **Node.js 20.x**: Runtime JavaScript
- **Python 3.11**: Runtime Python

---

## 🏗 Arquitetura do Sistema

### Estrutura de Diretórios

```
/app/
├── backend/
│   ├── server.py              # API FastAPI principal
│   ├── .env                   # Variáveis de ambiente
│   └── requirements.txt       # Dependências Python
│
├── frontend/
│   ├── src/
│   │   ├── App.js            # Componente principal
│   │   ├── App.css           # Estilos customizados
│   │   ├── index.js          # Entry point
│   │   └── components/ui/    # Componentes Shadcn UI
│   ├── package.json          # Dependências Node
│   └── .env                  # Variáveis de ambiente
│
└── PROJETO_DOCUMENTACAO.md   # Este arquivo
```

### Fluxo de Dados

```
1. Usuário cola URL da playlist
   ↓
2. Frontend → POST /api/playlist
   ↓
3. Backend extrai ID e consulta Spotify API
   ↓
4. Retorna metadados (nome, músicas, capas)
   ↓
5. Frontend exibe informações
   ↓
6. Usuário clica em "Baixar"
   ↓
7. Backend:
   - Busca música no YouTube (nome + artista)
   - Baixa áudio usando yt-dlp
   - Converte para MP3 com FFmpeg
   - Retorna arquivo
   ↓
8. Frontend inicia download no navegador
```

---

## 📝 Alterações Detalhadas

### Arquivo: `/app/backend/server.py`

#### **Criação Completa do Backend**

**1. Configuração Inicial**
```python
# Importações de bibliotecas necessárias
# Configuração do Spotify Client com credenciais
# Criação de rotas com prefixo /api
```

**2. Modelos Pydantic**
```python
class PlaylistRequest(BaseModel):
    url: str

class Track(BaseModel):
    id: str
    name: str
    artist: str
    album: str
    image_url: Optional[str]
    duration_ms: int

class PlaylistResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    image_url: Optional[str]
    total_tracks: int
    tracks: List[Track]
```

**3. Função de Extração de ID**
```python
def extract_playlist_id(url: str) -> str:
    """Extrai ID da playlist de URLs do Spotify"""
    # Suporta formatos:
    # - https://open.spotify.com/playlist/ID
    # - spotify:playlist:ID
```

**4. Função de Download do YouTube**
```python
def download_from_youtube(query: str, output_path: Path) -> bool:
    """
    Baixa áudio do YouTube e converte para MP3
    - Usa yt-dlp para buscar e baixar
    - Converte automaticamente para MP3 (192 kbps)
    - Retorna True se sucesso, False se falhar
    """
```

**5. Endpoint: GET /api/**
```python
@api_router.get("/")
async def root():
    return {"message": "Spotify Playlist Downloader API"}
```

**6. Endpoint: POST /api/playlist**
```python
@api_router.post("/playlist", response_model=PlaylistResponse)
async def get_playlist(request: PlaylistRequest):
    """
    Busca informações da playlist do Spotify
    
    Funcionalidades:
    - Extrai ID da URL
    - Consulta Spotify API com market='BR'
    - Filtra músicas válidas (com ID)
    - Retorna metadados completos
    - Trata erros específicos (404, 403, etc)
    """
```

**7. Endpoint: POST /api/download-track** ⚠️ **CORRIGIDO**
```python
@api_router.post("/download-track")
async def download_track(request: DownloadRequest):
    """
    Baixa uma música individual
    
    Melhorias aplicadas:
    - Retorna erro 404 com mensagem clara se falhar
    - Limpa diretórios temporários em caso de erro
    - Mensagem específica: "Não foi possível encontrar/baixar..."
    """
```

**8. Endpoint: POST /api/download-all** ⚠️ **CORRIGIDO**
```python
@api_router.post("/download-all")
async def download_all(request: DownloadAllRequest):
    """
    Baixa todas as músicas e cria ZIP
    
    Melhorias aplicadas:
    - Continua mesmo se algumas músicas falharem
    - Conta sucessos e falhas
    - Retorna headers X-Download-Summary
    - Cria ZIP apenas com músicas baixadas
    - Log detalhado de falhas
    """
```

### Arquivo: `/app/backend/.env`

**Adicionadas Credenciais do Spotify:**
```env
SPOTIFY_CLIENT_ID="d933d72aa7c74437973d7c81d858705f"
SPOTIFY_CLIENT_SECRET="b866b9e68d944ed5aef9ff5920b8d8f4"
```

### Arquivo: `/app/backend/requirements.txt`

**Bibliotecas Instaladas:**
```txt
spotipy         # Integração com Spotify API
yt-dlp          # Download e conversão de YouTube
redis           # Dependência do spotipy
```

### Arquivo: `/app/frontend/src/App.js`

#### **Criação Completa da Interface**

**1. Estados do React**
```javascript
const [playlistUrl, setPlaylistUrl] = useState("");
const [loading, setLoading] = useState(false);
const [playlist, setPlaylist] = useState(null);
const [downloadingTrack, setDownloadingTrack] = useState(null);
const [downloadingAll, setDownloadingAll] = useState(false);
const [progress, setProgress] = useState(0);
```

**2. Função: handleLoadPlaylist**
```javascript
const handleLoadPlaylist = async () => {
    // Valida URL
    // Faz POST para /api/playlist
    // Exibe toast de sucesso/erro
    // Atualiza estado com dados da playlist
}
```

**3. Função: handleDownloadTrack** ⚠️ **CORRIGIDA**
```javascript
const handleDownloadTrack = async (track) => {
    // Envia requisição para download individual
    // Cria blob e inicia download no navegador
    // CORREÇÃO: Parseia erro do backend corretamente
    // Exibe mensagem de erro específica em toast
}
```

**4. Função: handleDownloadAll** ⚠️ **CORRIGIDA**
```javascript
const handleDownloadAll = async () => {
    // Simula progresso visual
    // Envia todas as músicas para backend
    // CORREÇÃO: Lê headers X-Download-Summary
    // Exibe mensagem apropriada:
    //   - Sucesso total: "Todas as X músicas baixadas"
    //   - Parcial: "X de Y músicas baixadas. Algumas indisponíveis"
}
```

**5. Componentes JSX**

**Header:**
```jsx
<div className="text-center mb-12">
    <div className="bg-emerald-500/10 p-4 rounded-2xl">
        <Music className="w-12 h-12 text-emerald-400" />
    </div>
    <h1>SpotiDown</h1>
    <p>Baixe suas playlists favoritas...</p>
</div>
```

**Input de Playlist:**
```jsx
<Card data-testid="playlist-input-card">
    <Input data-testid="playlist-url-input" />
    <Button data-testid="load-playlist-button" />
</Card>
```

**Preview da Playlist:**
```jsx
<Card data-testid="playlist-content">
    <img data-testid="playlist-image" />
    <h2 data-testid="playlist-name" />
    <p data-testid="playlist-description" />
    <Button data-testid="download-all-button" />
    <Progress data-testid="download-progress" />
</Card>
```

**Lista de Músicas:**
```jsx
{playlist.tracks.map((track, index) => (
    <Card data-testid={`track-card-${index}`}>
        <img data-testid={`track-image-${index}`} />
        <h3 data-testid={`track-name-${index}`} />
        <p data-testid={`track-artist-${index}`} />
        <Button data-testid={`download-track-button-${index}`} />
    </Card>
))}
```

**Empty State:**
```jsx
<div data-testid="empty-state">
    <AlertCircle />
    <p>Nenhuma playlist carregada ainda</p>
</div>
```

### Arquivo: `/app/frontend/src/App.css`

**Estilização Custom:**
```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk...');

* {
  font-family: 'Space Grotesk', sans-serif;
}

body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}
```

### Arquivo: `/app/frontend/src/index.js`

**Adição do Toaster:**
```javascript
import { Toaster } from 'sonner';

root.render(
  <React.StrictMode>
    <App />
    <Toaster position="top-center" richColors />
  </React.StrictMode>
);
```

### Arquivo: `/app/frontend/package.json`

**Biblioteca Instalada:**
```json
"sonner": "^2.0.7"  // Sistema de notificações toast
```

---

## ⚙️ Como Funciona

### 1. Integração com Spotify

**Autenticação:**
- Usa Client Credentials Flow (não requer login do usuário)
- Credenciais armazenadas em variáveis de ambiente
- Token gerenciado automaticamente pelo spotipy

**Busca de Playlist:**
```python
# Extrai ID da URL
playlist_id = extract_playlist_id(url)

# Consulta API do Spotify com market BR
playlist = spotify_client.playlist(playlist_id, market='BR')

# Extrai informações
- Nome, descrição, imagem da playlist
- Para cada música: nome, artista, álbum, capa, duração
```

### 2. Download de Músicas

**Processo:**
```
1. Recebe nome e artista da música
   ↓
2. Monta query de busca: "Nome Artista"
   ↓
3. yt-dlp busca no YouTube (ytsearch1:query)
   ↓
4. Baixa melhor qualidade de áudio disponível
   ↓
5. FFmpeg converte para MP3 (192 kbps)
   ↓
6. Salva em diretório temporário
   ↓
7. Retorna arquivo via FileResponse
   ↓
8. Agenda limpeza do arquivo temporário
```

**Opções do yt-dlp:**
```python
{
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'default_search': 'ytsearch1:',  # Busca apenas 1 resultado
    'quiet': True,
    'no_warnings': True,
}
```

### 3. Download em Lote

**Processo:**
```
1. Recebe lista de todas as músicas
   ↓
2. Loop: Para cada música
   - Tenta baixar
   - Se sucesso: contador++
   - Se falha: adiciona à lista de falhas
   ↓
3. Cria arquivo ZIP com músicas baixadas
   ↓
4. Adiciona headers com resumo
   ↓
5. Retorna ZIP
   ↓
6. Frontend lê headers e exibe mensagem apropriada
```

### 4. Tratamento de Erros

**Backend:**
- Vídeo indisponível → Retorna 404 com mensagem
- Playlist privada → Retorna 403
- Playlist não encontrada → Retorna 404
- Erro geral → Retorna 500

**Frontend:**
- Parseia resposta blob em caso de erro
- Extrai mensagem JSON
- Exibe toast com mensagem específica

---

## ⚠️ Limitações e Observações

### Limitações Técnicas

1. **Playlists do Spotify:**
   - Apenas playlists **públicas** funcionam
   - Playlists geradas automaticamente pelo Spotify (ex: "Global Top 50") podem ter restrições regionais
   - Recomenda-se usar playlists criadas por usuários

2. **Disponibilidade no YouTube:**
   - Nem todas as músicas estão disponíveis no YouTube
   - Algumas podem estar bloqueadas por região
   - Músicas com restrição de idade não são baixadas
   - Vídeos privados ou removidos retornam erro

3. **Qualidade do Áudio:**
   - Depende da qualidade disponível no YouTube
   - Conversão fixa em 192 kbps MP3
   - Pode não ser qualidade lossless

4. **Performance:**
   - Downloads em lote podem demorar (depende da velocidade e número de músicas)
   - Processamento é sequencial (não paralelo)
   - Uso intensivo de CPU durante conversão

### Observações Importantes

1. **Uso Legal:**
   - A aplicação é para uso educacional/pessoal
   - Respeite direitos autorais
   - Baixe apenas conteúdo que você tem direito de acessar

2. **Arquivos Temporários:**
   - Downloads são salvos em `/tmp/spotify_downloads/`
   - Limpeza automática após download
   - Pode ocupar espaço em disco durante processo

3. **Rate Limits:**
   - Spotify API tem limites de requisição
   - YouTube pode bloquear IPs com muitas requisições
   - Recomenda-se uso moderado

4. **Nomenclatura:**
   - Arquivos MP3 seguem padrão: "Nome - Artista.mp3"
   - ZIP segue padrão: "playlist_id.zip"

---

## 📊 Resumo de Implementação

### Arquivos Criados
- `/app/backend/server.py` (259 linhas)
- `/app/frontend/src/App.js` (287 linhas)
- `/app/frontend/src/App.css` (8 linhas)
- `/app/frontend/src/index.js` (modificado)

### Arquivos Modificados
- `/app/backend/.env` (+ credenciais Spotify)
- `/app/backend/requirements.txt` (+ spotipy, yt-dlp)
- `/app/frontend/package.json` (+ sonner)

### Dependências Externas Instaladas
- **Backend:** spotipy, yt-dlp, redis
- **Frontend:** sonner
- **Sistema:** FFmpeg

### Endpoints API
- `GET /api/` - Health check
- `POST /api/playlist` - Buscar playlist
- `POST /api/download-track` - Download individual
- `POST /api/download-all` - Download em lote

### Componentes UI
- Card de input de playlist
- Preview de playlist com capa
- Lista de músicas com detalhes
- Botões de download individual
- Botão de download em lote
- Barra de progresso
- Sistema de toasts
- Empty state

---

## 🎨 Design e UX

### Paleta de Cores
- **Background:** Gradiente slate-950 → slate-900 → slate-950
- **Primária:** Emerald (400-600)
- **Secundária:** Teal (400-600)
- **Texto:** Slate (100-500)

### Tipografia
- **Font:** Space Grotesk (Google Fonts)
- **Pesos:** 400, 500, 600, 700

### Componentes Shadcn UI Utilizados
- Button
- Input
- Card (CardHeader, CardTitle, CardDescription, CardContent)
- Progress
- Toast (via Sonner)

### Ícones Lucide React
- Music (logo principal)
- Download (botões de download)
- Loader2 (estado de loading)
- AlertCircle (mensagens de erro)
- CheckCircle2 (sucesso - preparado)

---

## 🚀 Próximas Melhorias Sugeridas

1. **Performance:**
   - Download paralelo de múltiplas músicas
   - Cache de músicas já baixadas
   - Compressão otimizada do ZIP

2. **Funcionalidades:**
   - Pesquisa de playlists por nome
   - Histórico de downloads
   - Seleção individual de músicas para baixar
   - Preview de áudio antes do download

3. **UX:**
   - Dark/Light mode toggle
   - Progresso individual por música no download em lote
   - Arrastar e soltar URL
   - Compartilhamento de playlist

4. **Técnico:**
   - Testes unitários e integração
   - Dockerização
   - CI/CD pipeline
   - Monitoramento e logs

---

**Desenvolvido por:** E1 (Emergent AI Agent)  
**Data:** Outubro 2025  
**Versão:** 1.0.0
