import json
import docker
from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import DenyConnection
from .models import TerminalLabSession
import threading


class TerminalConsumer(WebsocketConsumer):
    """WebSocket consumer that bridges xterm.js to a Docker container's PTY."""

    def connect(self):
        """Establish WebSocket connection and attach to Docker container."""
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            raise DenyConnection("Authentication required")

        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.container_id = None
        self.exec_id = None
        self.docker_client = None
        self.docker_socket = None
        self.read_thread = None
        self.running = False
        self.command_buffer = ''
        self.command_history = []

        try:
            # Get the lab session
            session = TerminalLabSession.objects.get(
                id=self.session_id,
                user=user,
                status='active'
            )
            self.container_id = session.container_id

            if not self.container_id:
                raise DenyConnection("No container associated with this session")

            # Connect to Docker (auto-detects Windows named pipes / Linux unix sockets)
            self.docker_client = docker.from_env().api

            # Create an exec instance with PTY
            self.exec_id = self.docker_client.exec_create(
                self.container_id,
                cmd='/bin/bash',
                stdin=True,
                stdout=True,
                stderr=True,
                tty=True,
            )['Id']

            # Start the exec instance and get the socket
            self.docker_socket = self.docker_client.exec_start(
                self.exec_id,
                socket=True,
                tty=True,
            )

            self.accept()
            self.running = True

            # Start reading from Docker in a background thread
            self.read_thread = threading.Thread(target=self._read_from_docker, daemon=True)
            self.read_thread.start()

        except TerminalLabSession.DoesNotExist:
            raise DenyConnection("Invalid session")
        except Exception as e:
            raise DenyConnection(f"Docker connection failed: {str(e)}")

    def _get_socket(self):
        """Get the underlying raw socket, handling both Linux and Windows Docker."""
        if self.docker_socket is None:
            return None
        # On Linux, docker returns a SocketIO wrapper with _sock attribute
        # On Windows, docker returns NpipeSocket directly with send/recv
        if hasattr(self.docker_socket, '_sock'):
            return self.docker_socket._sock
        return self.docker_socket

    def disconnect(self, close_code):
        """Clean up when WebSocket disconnects."""
        self.running = False

        # Close Docker socket
        if self.docker_socket:
            try:
                self.docker_socket.close()
            except Exception:
                pass

    def receive(self, text_data=None, bytes_data=None):
        """Receive input from xterm.js and forward to Docker container."""
        sock = self._get_socket()
        if not sock or not self.running:
            return

        try:
            if text_data:
                data = text_data
            elif bytes_data:
                data = bytes_data.decode('utf-8', errors='replace')
            else:
                return

            # Initialize escape sequence state if not exists
            if not hasattr(self, 'in_escape'):
                self.in_escape = False

            # Track commands (capture on Enter key)
            for char in data:
                if self.in_escape:
                    # ANSI escape sequences typically end with a letter or a tilde
                    if char.isalpha() or char == '~':
                        self.in_escape = False
                    continue

                if char == '\x1b':
                    self.in_escape = True
                    continue

                if char == '\r' or char == '\n':
                    cmd = self.command_buffer.strip()
                    if cmd:
                        self.command_history.append(cmd)
                        # Send command history update to frontend
                        self.send(text_data=json.dumps({
                            'type': 'command_history',
                            'history': self.command_history,
                        }))
                    self.command_buffer = ''
                elif char in ('\x7f', '\x08'):  # Backspace
                    self.command_buffer = self.command_buffer[:-1]
                elif ord(char) >= 32:  # Printable characters
                    self.command_buffer += char

            # Forward to Docker
            sock.sendall(data.encode('utf-8'))

        except Exception as e:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error sending to terminal: {str(e)}'
            }))

    def _read_from_docker(self):
        """Background thread: read Docker output and send to WebSocket."""
        sock = self._get_socket()
        if not sock:
            return

        try:
            while self.running:
                data = sock.recv(4096)
                if not data:
                    break

                try:
                    text = data.decode('utf-8', errors='replace')
                    self.send(text_data=json.dumps({
                        'type': 'output',
                        'data': text,
                    }))
                except Exception:
                    break
        except Exception:
            pass
        finally:
            self.running = False
            try:
                self.close()
            except Exception:
                pass
