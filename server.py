import http.server
import socketserver
import os
import urllib.parse
import qrcode
import socket
import time
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
import mimetypes
import string
import getpass
import secrets
from http import cookies
import colorama
from colorama import Fore, Style

colorama.init()

def get_default_download_path():
    """Get the default downloads folder path"""
    home = Path.home()
    if os.name == 'nt':  # Windows
        return home / 'Downloads'
    return home / 'Downloads'  # Linux/Mac

# Configuration
PORT = 8000
# Set ROOT_DIRECTORY to the user's Downloads directory
ROOT_DIRECTORY = str(get_default_download_path())
ALLOWED_PATHS = [
    str(Path.home()),  # User's home directory
    str(Path.home() / "Documents"),
    str(Path.home() / "Downloads"),
    str(Path.home() / "Pictures"),
    str(Path.home() / "Music"),
    str(Path.home() / "Videos"),
    str(Path.home() / "Desktop"),
]

SERVER_PASSWORD = getpass.getpass('Enter access key (leave blank for no password): ')
SESSION_SECRET = secrets.token_hex(16)
SESSIONS = set()

# Detect all available drives (Windows)
def get_windows_drives():
    if os.name != 'nt':
        return []
    drives = []
    for letter in string.ascii_uppercase:
        drive = f'{letter}:'
        if os.path.exists(f'{drive}\\'):
            drives.append(drive)
    return drives

# Extend allowed paths to include all drives without changing ROOT_DIRECTORY
ALL_DRIVES = get_windows_drives()
ALLOWED_PATHS.extend([f'{d}\\' for d in ALL_DRIVES])

def is_path_allowed(path):
    """Check if the path is within allowed directories"""
    try:
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(allowed) for allowed in ALLOWED_PATHS)
    except:
        return False

def get_relative_path(path):
    """Convert absolute path to relative path from root directory"""
    try:
        return os.path.relpath(path, ROOT_DIRECTORY)
    except:
        return path

def get_terminal_size():
    """Get terminal size for better formatting"""
    try:
        columns, rows = shutil.get_terminal_size()
        return columns, rows
    except:
        return 80, 24

def print_header():
    """Print a fancy header"""
    columns, _ = get_terminal_size()
    print("\n" + "=" * columns)
    print("🎥 File Browser Server".center(columns))
    print("=" * columns + "\n")

def print_status(message, status_type="info"):
    """Print a status message with appropriate emoji"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "upload": "📤",
        "download": "📥",
        "file": "📁",
        "server": "🌐",
        "directory": "📂"
    }.get(status_type, "ℹ️")
    print(f"[{timestamp}] {emoji} {message}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def load_config():
    """Load configuration from config.json"""
    config_path = Path('config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'download_path': str(get_default_download_path())}

def save_config(config):
    """Save configuration to config.json"""
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

def format_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def generate_qr_code(url):
    """Generate and format QR code for terminal display"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Get QR matrix
    qr_matrix = qr.get_matrix()
    
    # Calculate padding to make it more square and match terminal width
    columns, _ = get_terminal_size()
    qr_width = len(qr_matrix[0])
    padding = " " * ((columns - qr_width) // 2)
    
    # Generate ASCII art with better contrast
    ascii_qr = ""
    for row in qr_matrix:
        ascii_qr += padding + "".join("█" if cell else " " for cell in row) + "\n"
    
    return ascii_qr

def get_file_icon(filename):
    """Get appropriate icon for file type"""
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        # Images
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️',
        # Documents
        '.pdf': '📄', '.doc': '📄', '.docx': '📄', '.txt': '📄', '.rtf': '📄',
        # Audio
        '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵', '.m4a': '🎵',
        # Video
        '.mp4': '🎥', '.avi': '🎥', '.mov': '🎥', '.wmv': '🎥',
        # Archives
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        # Code
        '.py': '📝', '.js': '📝', '.html': '📝', '.css': '📝', '.json': '📝',
    }
    return icons.get(ext, '📄')

# Generate server URL and QR code
local_ip = get_local_ip()
server_url = f"http://{local_ip}:{PORT}"
ascii_qr = generate_qr_code(server_url)

def show_intro():
    print(Fore.CYAN + r"""
███████╗██╗██╗     ███████╗    ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ 
██╔════╝██║██║     ██╔════╝    ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
█████╗  ██║██║     █████╗      ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
██╔══╝  ██║██║     ██╔══╝      ╚════██║██╔══╝  ██╔══██╗██║   ██║██╔══╝  ██╔══██╗
██║     ██║███████╗███████╗    ███████║███████╗██║  ██║╚██████╔╝███████╗██║  ██║
╚═╝     ╚═╝╚══════╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
    """ + Style.RESET_ALL)
    time.sleep(2)  # Delay for 2 seconds
    print(Fore.GREEN + "                      Lightweight Web-Based File Server | v1.0" + Style.RESET_ALL)
    time.sleep(1)  # Delay for 1 second
    print(Fore.YELLOW + "                      Author: Ham (https://github.com/cecamarty)" + Style.RESET_ALL)
    time.sleep(1)  # Delay for 1 second
    print(Fore.BLUE + "                     GitHub: https://github.com/cecamarty/FileServer" + Style.RESET_ALL)

print_status("Author / Credits: Ham (https://github.com/cecamarty)", "info")

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to provide more detailed logging"""
        print_status(format % args, "server")

    def do_GET(self):
        try:
            # Check authentication first
            if SERVER_PASSWORD and not self.is_authenticated():
                if self.path == '/login':
                    self.serve_login_page()
                else:
                    self.send_response(303)
                    self.send_header('Location', '/login')
                    self.end_headers()
                return

            path = urllib.parse.unquote(self.path)

            # Serve landing page at root
            if path == '/':
                self.serve_landing_page()
                return

            # Serve file browser at /browse/ and subdirectories
            if path.startswith('/browse'):
                browse_path = path[len('/browse'):]
                if browse_path == '' or browse_path == '/':
                    self.list_directory('/', drives=ALL_DRIVES)
                else:
                    self.list_directory(browse_path, drives=ALL_DRIVES)
                return

            # Directory search endpoint
            if path.startswith('/search'):
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                dir_path = query.get('dir', ['/'])[0]
                search_term = query.get('q', [''])[0].lower()
                abs_dir = os.path.join(ROOT_DIRECTORY, dir_path.lstrip('/'))
                if not is_path_allowed(abs_dir):
                    self.send_error(403, "Access denied")
                    return
                results = []
                for root, dirs, files in os.walk(abs_dir):
                    for name in dirs + files:
                        if search_term in name.lower():
                            rel_path = os.path.relpath(os.path.join(root, name), ROOT_DIRECTORY)
                            results.append(rel_path.replace('\\', '/'))
                    break  # Only search current dir, remove to search recursively
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'results': results}).encode())
                return

            # API endpoints
            if path == '/config':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'root_directory': ROOT_DIRECTORY,
                    'allowed_paths': ALLOWED_PATHS,
                    'drives': ALL_DRIVES
                }).encode())
                return

            # Handle file downloads and directory redirection
            file_path = os.path.join(ROOT_DIRECTORY, path.lstrip('/'))
            if not is_path_allowed(file_path):
                self.send_error(403, "Access denied")
                return

            if os.path.isdir(file_path):
                self.send_response(301)
                self.send_header('Location', '/browse' + path + ('/' if not path.endswith('/') else ''))
                self.end_headers()
                return

            if os.path.isfile(file_path):
                if file_path.endswith('.html'):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                self.send_file(file_path)
                return

            self.send_error(404, "Not found")
            return
        except Exception as e:
            print_status(f"Error handling request: {str(e)}", "error")
            self.send_error(500, str(e))

    def serve_landing_page(self):
        html = '''<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="google-site-verification" content="5CvI1z1MN1nf65qyNlxloDCemJ-EC5jXGCf0glG3l-I" />
            <title>FileServer - Home</title>
            <style>
                :root {
                    --bg: #1e1e1e;
                    --panel: #252526;
                    --primary: #569cd6;
                    --secondary: #4ec9b0;
                    --text: #d4d4d4;
                    --accent: #d7ba7d;
                    --border: #333;
                }
                body {
                    background: var(--bg);
                    color: var(--text);
                    font-family: 'Consolas', 'Courier New', monospace;
                    margin: 0;
                    min-height: 100vh;
                }
                .container {
                    max-width: 500px;
                    margin: 2rem auto;
                    background: var(--panel);
                    border-radius: 8px;
                    box-shadow: 0 2px 16px #0008;
                    padding: 2rem 1.5rem 1.5rem 1.5rem;
                    border: 1px solid var(--border);
                }
                h1 {
                    text-align: center;
                    color: var(--primary);
                    margin-bottom: 0.5em;
                }
                .actions {
                    display: flex;
                    gap: 1rem;
                    justify-content: center;
                    margin-bottom: 2rem;
                }
                .action-btn {
                    flex: 1;
                    background: var(--bg);
                    color: var(--primary);
                    border: 2px solid var(--primary);
                    border-radius: 6px;
                    font-size: 1.1rem;
                    padding: 0.8em 0;
                    cursor: pointer;
                    transition: background 0.2s, color 0.2s;
                }
                .action-btn.selected, .action-btn:hover {
                    background: var(--primary);
                    color: var(--bg);
                }
                .section {
                    display: none;
                }
                .section.active {
                    display: block;
                }
                .upload-area {
                    border: 2px dashed var(--primary);
                    border-radius: 8px;
                    padding: 2rem;
                    text-align: center;
                    background: #2228;
                    margin-bottom: 1rem;
                    cursor: pointer;
                }
                .upload-area label {
                    color: var(--primary);
                    font-weight: 500;
                    cursor: pointer;
                }
                .upload-area .icon {
                    font-size: 2.5rem;
                    margin-bottom: 0.5rem;
                }
                .upload-area input[type="file"] {
                    display: none;
                }
                .progress {
                    display: none;
                    margin-top: 1rem;
                    text-align: center;
                }
                .progress.active {
                    display: block;
                }
                .progress-bar {
                    width: 100%;
                    height: 4px;
                    background-color: #444;
                    border-radius: 2px;
                    overflow: hidden;
                    margin-top: 0.5rem;
                }
                .progress-bar-fill {
                    height: 100%;
                    background-color: var(--primary);
                    width: 0%;
                    transition: width 0.3s ease;
                }
                .browse-link {
                    display: block;
                    text-align: center;
                    margin-top: 2rem;
                    color: var(--secondary);
                    font-size: 1.1rem;
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>FileServer</h1>
                <div class="actions">
                    <button class="action-btn selected" id="addBtn">Add Files</button>
                    <button class="action-btn" id="browseBtn">Browse Files</button>
                </div>
                <div class="section active" id="addSection">
                    <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
                        <div class="upload-area" id="dropZone">
                            <div class="icon">📁</div>
                            <label for="fileInput">Click to select or drag files here</label>
                            <input type="file" id="fileInput" name="file" multiple>
                        </div>
                        <div class="progress" id="progress">
                            <p>Uploading... <span id="progressText">0%</span></p>
                            <div class="progress-bar">
                                <div class="progress-bar-fill" id="progressBarFill"></div>
                            </div>
                        </div>
                        <button type="submit" style="width:100%;margin-top:1rem;background:var(--primary);color:var(--bg);border:none;padding:0.8em 0;border-radius:6px;font-size:1rem;">Upload Files</button>
                    </form>
                </div>
                <div class="section" id="browseSection">
                    <a href="/browse/" class="browse-link">Go to File Browser &rarr;</a>
                </div>
            </div>
            <script>
                const addBtn = document.getElementById('addBtn');
                const browseBtn = document.getElementById('browseBtn');
                const addSection = document.getElementById('addSection');
                const browseSection = document.getElementById('browseSection');
                addBtn.onclick = () => {
                    addBtn.classList.add('selected');
                    browseBtn.classList.remove('selected');
                    addSection.classList.add('active');
                    browseSection.classList.remove('active');
                };
                browseBtn.onclick = () => {
                    browseBtn.classList.add('selected');
                    addBtn.classList.remove('selected');
                    browseSection.classList.add('active');
                    addSection.classList.remove('active');
                };
                // Upload logic
                const dropZone = document.getElementById('dropZone');
                const fileInput = document.getElementById('fileInput');
                const uploadForm = document.getElementById('uploadForm');
                const progress = document.getElementById('progress');
                const progressText = document.getElementById('progressText');
                const progressBarFill = document.getElementById('progressBarFill');
                const pendingList = document.createElement('ul');
                pendingList.style.marginTop = '1em';
                pendingList.style.color = '#d7ba7d';
                pendingList.style.fontFamily = 'Consolas, monospace';
                dropZone.parentNode.appendChild(pendingList);

                function updatePendingList() {
                    pendingList.innerHTML = '';
                    for (let i = 0; i < fileInput.files.length; i++) {
                        const li = document.createElement('li');
                        li.textContent = fileInput.files[i].name;
                        pendingList.appendChild(li);
                    }
                }

                fileInput.addEventListener('change', updatePendingList);
                dropZone.addEventListener('drop', (e) => {
                    setTimeout(updatePendingList, 10);
                });

                uploadForm.addEventListener('submit', (e) => {
                    if (fileInput.files.length === 0) {
                        alert('Please select files to upload.');
                        e.preventDefault();
                        return;
                    }
                    e.preventDefault();
                    const formData = new FormData(uploadForm);
                    progress.classList.add('active');
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', '/upload', true);
                    xhr.upload.onprogress = (e) => {
                        if (e.lengthComputable) {
                            const percentComplete = (e.loaded / e.total) * 100;
                            progressText.textContent = `${Math.round(percentComplete)}%`;
                            progressBarFill.style.width = `${percentComplete}%`;
                        }
                    };
                    xhr.onload = () => {
                        progress.classList.remove('active');
                        progressText.textContent = '0%';
                        progressBarFill.style.width = '0%';
                        if (xhr.status === 200 || xhr.status === 303) {
                            alert('Upload successful!');
                            pendingList.innerHTML = '';
                            fileInput.value = '';
                            uploadForm.reset();
                        } else {
                            alert('Upload failed.');
                        }
                    };
                    xhr.onerror = () => {
                        progress.classList.remove('active');
                        alert('Upload failed.');
                    };
                    xhr.send(formData);
                });
            </script>
        </body>
        </html>'''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def send_file(self, file_path):
        """Send a file to the client"""
        try:
            file_size = os.path.getsize(file_path)
            print_status(f"Sending file: {file_path} ({format_size(file_size)})", "download")
            
            # Get the file's mime type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            print_status(f"Error sending file: {str(e)}", "error")
            self.send_error(500, str(e))

    def list_directory(self, path, drives=None):
        """List directory contents with a modern interface"""
        try:
            # Get the full path
            full_path = os.path.join(ROOT_DIRECTORY, path.lstrip('/'))
            if not is_path_allowed(full_path):
                self.send_error(403, "Access denied")
                return
                
            if not os.path.exists(full_path):
                self.send_error(404, "Directory not found")
                return

            # Get directory contents
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if not is_path_allowed(item_path):
                    continue
                    
                is_dir = os.path.isdir(item_path)
                size = 0 if is_dir else os.path.getsize(item_path)
                items.append({
                    'name': item,
                    'is_dir': is_dir,
                    'size': size,
                    'icon': '📂' if is_dir else get_file_icon(item)
                })

            # Sort: directories first, then files
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

            # Add drive selector and search bar to HTML
            drives = drives or []
            drive_selector = ''
            if drives:
                drive_selector = '<select id="driveSelect" style="margin-bottom:1rem;">' + ''.join(f'<option value="{d}:\\">{d}:</option>' for d in drives) + '</select>'
            search_bar = '''<input type="text" id="searchInput" placeholder="Search files/folders..." style="width:60%;margin-bottom:1rem;"> <button id="searchBtn">Search</button>'''

            # Generate HTML
            html = f'''<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta name="google-site-verification" content="5CvI1z1MN1nf65qyNlxloDCemJ-EC5jXGCf0glG3l-I" />
                <title>File Browser - {path}</title>
                <style>
                    :root {{
                        --bg-color: #1e1e1e;
                        --text-color: #d4d4d4;
                        --primary-color: #569cd6;
                        --secondary-color: #4ec9b0;
                        --border-color: #333;
                        --hover-color: #2d2d2d;
                        --file-bg: #252526;
                        --header-bg: #252526;
                    }}
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: 'Consolas', 'Courier New', monospace;
                        line-height: 1.6;
                        color: var(--text-color);
                        background-color: var(--bg-color);
                        padding: 1rem;
                        max-width: 800px;
                        margin: 0 auto;
                    }}
                    .header {{
                        background: var(--header-bg);
                        padding: 1rem;
                        border-radius: 4px;
                        margin-bottom: 1rem;
                        border: 1px solid var(--border-color);
                    }}
                    .path {{
                        color: var(--primary-color);
                        font-weight: 500;
                        word-break: break-all;
                        font-family: 'Consolas', 'Courier New', monospace;
                    }}
                    .file-list {{
                        list-style: none;
                    }}
                    .file-item {{
                        background: var(--file-bg);
                        padding: 0.8rem;
                        margin: 0.3rem 0;
                        border-radius: 4px;
                        display: flex;
                        align-items: center;
                        gap: 1rem;
                        border: 1px solid var(--border-color);
                        transition: background-color 0.2s;
                    }}
                    .file-item:hover {{
                        background-color: var(--hover-color);
                    }}
                    .file-icon {{
                        font-size: 1.2rem;
                        color: var(--secondary-color);
                    }}
                    .file-name {{
                        flex-grow: 1;
                        word-break: break-all;
                        font-family: 'Consolas', 'Courier New', monospace;
                    }}
                    .file-size {{
                        color: #888;
                        font-size: 0.9rem;
                        font-family: 'Consolas', 'Courier New', monospace;
                    }}
                    a {{
                        color: var(--primary-color);
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                    .upload-area {{
                        border: 2px dashed var(--border-color);
                        border-radius: 4px;
                        padding: 2rem;
                        text-align: center;
                        margin: 1rem 0;
                        background-color: var(--file-bg);
                        cursor: pointer;
                        transition: border-color 0.2s;
                    }}
                    .upload-area:hover {{
                        border-color: var(--primary-color);
                    }}
                    .upload-area input[type="file"] {{
                        display: none;
                    }}
                    .upload-area label {{
                        display: block;
                        cursor: pointer;
                        color: var(--primary-color);
                        font-weight: 500;
                    }}
                    .upload-area .icon {{
                        font-size: 2rem;
                        margin-bottom: 0.5rem;
                        color: var(--secondary-color);
                    }}
                    .progress {{
                        display: none;
                        margin-top: 1rem;
                        text-align: center;
                    }}
                    .progress.active {{
                        display: block;
                    }}
                    .progress-bar {{
                        width: 100%;
                        height: 4px;
                        background-color: var(--border-color);
                        border-radius: 2px;
                        overflow: hidden;
                        margin-top: 0.5rem;
                    }}
                    .progress-bar-fill {{
                        height: 100%;
                        background-color: var(--primary-color);
                        width: 0%;
                        transition: width 0.3s ease;
                    }}
                    @media (max-width: 600px) {{
                        body {{
                            padding: 0.5rem;
                        }}
                        .file-item {{
                            padding: 0.8rem;
                        }}
                        .file-size {{
                            display: none;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>FileServer</h1>
                    {drive_selector}
                    {search_bar}
                    <div class="path" id="currentPath">{path}</div>
                </div>
                
                <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="path" id="uploadPath" value="{path}">
                    <div class="upload-area" id="dropZone">
                        <div class="icon">📁</div>
                        <label for="fileInput">Click to select or drag files here</label>
                        <input type="file" id="fileInput" name="file" multiple>
                    </div>
                    <div class="progress" id="progress">
                        <p>Uploading... <span id="progressText">0%</span></p>
                        <div class="progress-bar">
                            <div class="progress-bar-fill" id="progressBarFill"></div>
                        </div>
                    </div>
                </form>

                <ul class="file-list">
                    <li class="file-item">
                        <span class="file-icon">⬆️</span>
                        <a href="{os.path.dirname(path)}" class="file-name">..</a>
                    </li>
                    {''.join(f'''
                    <li class="file-item">
                        <span class="file-icon">{item['icon']}</span>
                        <a href="{os.path.join(path, item['name'])}" class="file-name">{item['name']}</a>
                        <span class="file-size">{format_size(item['size']) if not item['is_dir'] else ''}</span>
                    </li>
                    ''' for item in items)}
                </ul>

                <script>
                    const dropZone = document.getElementById('dropZone');
                    const fileInput = document.getElementById('fileInput');
                    const uploadForm = document.getElementById('uploadForm');
                    const progress = document.getElementById('progress');
                    const progressText = document.getElementById('progressText');
                    const progressBarFill = document.getElementById('progressBarFill');

                    // Drag and drop handlers
                    dropZone.addEventListener('dragover', (e) => {{
                        e.preventDefault();
                        dropZone.style.borderColor = 'var(--primary-color)';
                    }});

                    dropZone.addEventListener('dragleave', () => {{
                        dropZone.style.borderColor = 'var(--border-color)';
                    }});

                    dropZone.addEventListener('drop', (e) => {{
                        e.preventDefault();
                        dropZone.style.borderColor = 'var(--border-color)';
                        fileInput.files = e.dataTransfer.files;
                    }});

                    // Click to upload
                    dropZone.addEventListener('click', () => {{
                        fileInput.click();
                    }});

                    // File input change handler
                    fileInput.addEventListener('change', () => {{
                        if (fileInput.files.length > 0) {{
                            uploadForm.submit();
                        }}
                    }});

                    // Form submission
                    uploadForm.addEventListener('submit', (e) => {{
                        e.preventDefault();
                        const formData = new FormData(uploadForm);
                        
                        progress.classList.add('active');
                        
                        const xhr = new XMLHttpRequest();
                        xhr.open('POST', '/upload', true);

                        xhr.upload.onprogress = (e) => {{
                            if (e.lengthComputable) {{
                                const percentComplete = (e.loaded / e.total) * 100;
                                progressText.textContent = `${{Math.round(percentComplete)}}%`;
                                progressBarFill.style.width = `${{percentComplete}}%`;
                            }}
                        }};

                        xhr.onload = () => {{
                            if (xhr.status === 303) {{
                                const newPath = xhr.getResponseHeader('Location');
                                window.location.href = newPath;
                            }}
                        }};

                        xhr.onerror = () => {{
                            progress.textContent = 'Upload failed. Please try again.';
                            progress.classList.remove('active');
                        }};

                        xhr.send(formData);
                    }});

                    // Drive selector logic
                    const driveSelect = document.getElementById('driveSelect');
                    if (driveSelect) {{
                        driveSelect.value = '{ROOT_DIRECTORY.replace('\\', '\\\\')}';
                        driveSelect.onchange = function() {{
                            window.location.href = '/browse/' + driveSelect.value.replace(':\\\', '');
                        }};
                    }}

                    // Search logic
                    const searchInput = document.getElementById('searchInput');
                    const searchBtn = document.getElementById('searchBtn');
                    searchBtn.onclick = function() {{
                        const q = searchInput.value.trim();
                        if (!q) return;
                        fetch(`/search?dir=${{encodeURIComponent('{path}')}}&q=${{encodeURIComponent(q)}}`)
                            .then(r => r.json())
                            .then(data => {{
                                const fileList = document.querySelector('.file-list');
                                fileList.innerHTML = data.results.map(item => `<li class='file-item'><a href='/browse/${item}' class='file-name'>${item}</a></li>`).join('');
                            }});
                    }};
                </script>
            </body>
            </html>'''

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode())

        except Exception as e:
            print_status(f"Error listing directory: {str(e)}", "error")
            self.send_error(500, str(e))

    def do_POST(self):
        if self.path == '/upload':
            try:
                content_type = self.headers['Content-Type']
                if not content_type or not content_type.startswith('multipart/form-data'):
                    self.send_error(400, "Bad Request: Expected multipart/form-data")
                    return

                print_status("Receiving file upload...", "upload")
                start_time = time.time()

                # Get the boundary from the content type
                boundary = content_type.split('boundary=')[1].encode()
                
                # Read the request body
                content_length = int(self.headers['Content-Length'])
                print_status(f"File size: {format_size(content_length)}", "file")
                post_data = self.rfile.read(content_length)
                
                # Split the multipart data
                parts = post_data.split(b'--' + boundary)
                
                files_uploaded = 0
                upload_path = None

                for part in parts:
                    if b'name="path"' in part:
                        # Extract upload path
                        content_start = part.find(b'\r\n\r\n') + 4
                        content_end = part.rfind(b'\r\n')
                        upload_path = part[content_start:content_end].decode()
                        continue

                    if b'filename=' in part:
                        # Extract filename
                        filename_start = part.find(b'filename="') + 10
                        filename_end = part.find(b'"', filename_start)
                        filename = part[filename_start:filename_end].decode()
                        
                        if not filename:
                            print_status("Skipping file with empty filename", "warning")
                            continue
                        
                        # Create full path for the file
                        if upload_path:
                            file_path = os.path.join(ROOT_DIRECTORY, upload_path.lstrip('/'), filename)
                        else:
                            file_path = os.path.join(ROOT_DIRECTORY, filename)
                            
                        if not is_path_allowed(file_path):
                            print_status(f"Access denied: {file_path}", "error")
                            continue
                        
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        print_status(f"Saving file: {file_path}", "file")
                        
                        # Extract file content
                        content_start = part.find(b'\r\n\r\n') + 4
                        content_end = part.rfind(b'\r\n')
                        file_content = part[content_start:content_end]
                        
                        # Save the file
                        with open(file_path, 'wb') as f:
                            f.write(file_content)
                        files_uploaded += 1
                
                if files_uploaded == 0:
                    print_status("No files were uploaded", "warning")
                    self.send_error(400, "No files were uploaded")
                    return
                
                upload_time = time.time() - start_time
                print_status(f"Upload completed in {upload_time:.1f} seconds", "success")
                print_status(f"Successfully uploaded {files_uploaded} file(s)", "success")
                
                # Redirect back to the current directory
                self.send_response(303)
                self.send_header('Location', upload_path or '/')
                self.end_headers()
                
            except Exception as e:
                print_status(f"Error during upload: {str(e)}", "error")
                self.send_error(500, f"Internal Server Error: {str(e)}")

        elif self.path == '/login':
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(post_data)
            password = params.get('password', [''])[0]
            if password == SERVER_PASSWORD:
                session_id = secrets.token_hex(16)
                SESSIONS.add(session_id)
                self.send_response(303)
                self.send_header('Set-Cookie', f'session={session_id}; Path=/')
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.serve_login_page(error='Invalid password')
            return

    def is_authenticated(self):
        if not SERVER_PASSWORD:
            return True
        if 'Cookie' in self.headers:
            c = cookies.SimpleCookie(self.headers['Cookie'])
            session = c.get('session')
            if session and session.value in SESSIONS:
                return True
        return False

    def serve_login_page(self, error=None):
        html = f'''<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="google-site-verification" content="5CvI1z1MN1nf65qyNlxloDCemJ-EC5jXGCf0glG3l-I" />
            <title>FileServer Login</title>
            <style>
                body {{ background: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; }}
                .container {{ max-width: 400px; margin: 5em auto; background: #252526; border-radius: 8px; box-shadow: 0 2px 16px #0008; padding: 2em; border: 1px solid #333; }}
                h1 {{ color: #569cd6; text-align: center; }}
                input[type=password] {{ width: 100%; padding: 0.8em; border-radius: 6px; border: 1px solid #333; background: #1e1e1e; color: #d4d4d4; margin-bottom: 1em; }}
                button {{ width: 100%; background: #569cd6; color: #1e1e1e; border: none; border-radius: 6px; padding: 0.8em; font-size: 1em; cursor: pointer; }}
                .error {{ color: #f44336; text-align: center; margin-bottom: 1em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>FileServer Login</h1>
                {f'<div class="error">{error}</div>' if error else ''}
                <form method="POST" action="/login">
                    <input type="password" name="password" placeholder="Enter access key" autofocus required>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>'''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

# Print server startup information
show_intro()
print_status(f"Server URL: {server_url}", "server")
print_status(f"Root directory: {ROOT_DIRECTORY}", "file")
print("\n📱 Scan this QR code to access the server from your mobile device:")
print(ascii_qr)
print("\n" + "=" * get_terminal_size()[0])
print_status("Server is running. Press Ctrl+C to stop.", "info")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n" + "=" * get_terminal_size()[0])
        print_status("Server stopped by user", "info")
        sys.exit(0)
