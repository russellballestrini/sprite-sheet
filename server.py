#!/usr/bin/env python3
"""
Simple HTTP server with proper MIME types for JavaScript modules.
"""
import http.server
import socketserver
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Set proper MIME type for JavaScript files
        if self.path.endswith('.js'):
            self.send_header('Content-Type', 'application/javascript; charset=utf-8')
        elif self.path.endswith('.mjs'):
            self.send_header('Content-Type', 'application/javascript; charset=utf-8')
        super().end_headers()

    def guess_type(self, path):
        """Override to ensure .js files get the correct MIME type"""
        mimetype = super().guess_type(path)
        if path.endswith('.js') or path.endswith('.mjs'):
            return 'application/javascript'
        return mimetype

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}/")
        print(f"\nOpen your browser to:")
        print(f"  • http://localhost:{PORT}/demo.html")
        print(f"  • http://localhost:{PORT}/examples/simple-game.html")
        print(f"  • http://localhost:{PORT}/examples/sprite-atlas.html")
        print(f"\nPress Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
