# Honeypot Project

## Overview
This project simulates multiple services (HTTP, FTP, AWS Listener, etc.) acting as a **Honeypot**.  
The system is designed to attract attackers, log their attempts, and generate reports for security analysis and research purposes.

## Technologies
- Python 3.11  
- Flask  
- Docker & Docker Compose  
- ReportLab (report generation)

## Project Structure
```
controller/       # Controllers and Dockerfiles
model/            # Trap logic and report generator
view/             # Frontend (UI)
logs/             # Collected logs
reports/          # Generated reports
tests/            # Unit and integration tests
```

## Installation & Run
1. Clone the repository:
   ```bash
   git clone https://github.com/YarinGub/HoneyPot-Project.git
   cd HoneyPot-Project
   ```

2. Install dependencies (without Docker):
   ```bash
   pip install -r requirements.txt
   ```

3. Run with Docker:
   ```bash
   docker-compose up --build
   ```

## Usage
- **Health check**:
  ```bash
  curl http://localhost:5000/health
  ```

- **Send data to a trap**:
  ```bash
  curl -X POST http://localhost:5000/ingest     -H "Content-Type: application/json"     -d '{"trap_type": "http", "input": {"method": "GET", "path": "/"}}'
  ```

## Contributing
Feel free to open issues or submit pull requests if you’d like to improve the project.

