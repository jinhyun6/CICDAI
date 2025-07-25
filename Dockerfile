FROM python:3.9-slim

WORKDIR /app

RUN pip install Flask

# Create app.py file with proper escaping
RUN echo 'from flask import Flask' > app.py &&     echo 'import os' >> app.py &&     echo '' >> app.py &&     echo 'app = Flask(__name__)' >> app.py &&     echo '' >> app.py &&     echo '@app.route("/")' >> app.py &&     echo 'def hello():' >> app.py &&     echo '    return "<h1>🎉 CI/CD Success! Your app is deployed on Cloud Run!</h1>"' >> app.py &&     echo '' >> app.py &&     echo 'if __name__ == "__main__":' >> app.py &&     echo '    port = int(os.environ.get("PORT", 8080))' >> app.py &&     echo '    app.run(host="0.0.0.0", port=port)' >> app.py

EXPOSE 8080

CMD ["python", "app.py"]
