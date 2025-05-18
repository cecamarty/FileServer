# FileServer

A simple file server that allows you to browse and upload files from your local machine.

## Features

- Browse files and directories
- Upload files
- Search for files
- QR code for easy access from mobile devices

## Requirements

- Python 3.x
- Required Python packages:
  - `http.server`
  - `socketserver`
  - `qrcode`
  - `mimetypes`
  - `secrets`
  - `getpass`

## Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:cecamarty/FileServer.git
   cd <repository-directory>
   ```

2. Install the required packages:
   ```bash
   pip install qrcode
   ```

## Usage

1. Run the server:
   ```bash
   python server.py
   ```

2. Access the server in your web browser at `http://localhost:8000`.

3. Scan the QR code displayed in the terminal to access the server from your mobile device.

## Configuration

- The server uses the user's Downloads directory as the root directory by default.
- You can set a password for access by entering it when prompted.

## License

This project is licensed under the MIT License. 