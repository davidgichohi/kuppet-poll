from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Default to 5000 if not set
    app.run(host='0.0.0.0', port=port)
