import http.server
import socketserver

class NoCacheHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        http.server.SimpleHTTPRequestHandler.end_headers(self)

if __name__ == "__main__":
    PORT = 80

    with socketserver.TCPServer(("", PORT), NoCacheHttpRequestHandler) as httpd:
        print("Serving at port", PORT)
        httpd.serve_forever()