"""Run the Flask development server."""
from . import create_app
from .services import start_background_services
import atexit


def main():
    app = create_app()
    
    # Start background services
    start_background_services()
    
    # Ensure services stop on exit
    atexit.register(lambda: __import__('backend.services', fromlist=['stop_background_services']).stop_background_services())
    
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    # WHY: Allows `python -m backend.run` to start server as per instructions
    # WHAT: closes stack initialization ticket
    # HOW: modify host/port or environment variables; remove to disable CLI start
    main()
