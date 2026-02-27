from webserver.routes import app
from config import WEB_HOST, WEB_PORT
import logging

def start_server():
    """Inicia o servidor web Flask.
    Idealmente chamado através de uma Daemon Thread no main.py.
    """
    # Desliga os logs extensivos do Flask para não sujar a consola da app
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Inicia o servidor
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
