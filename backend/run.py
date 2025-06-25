"""Run the Flask development server."""
from . import create_app


def main():
    app = create_app()
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    # WHY: Allows `python -m backend.run` to start server as per instructions
    # WHAT: closes stack initialization ticket
    # HOW: modify host/port or environment variables; remove to disable CLI start
    main()
