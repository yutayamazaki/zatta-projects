from models import HTTPServer


if __name__ == '__main__':
    server = HTTPServer(host='127.0.0.1', port=8000)
    server.run()
