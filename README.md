# 🐑 Sheep Weight & Carcass Composition AI

A mobile AI solution for precision livestock monitoring. This project uses a fine-tuned ResNet18 model to predict sheep weight and carcass composition from images, integrated into a desktop application with user management and historical analytics.

## 🚀 New & Enhanced Features
- **User Authentication System:** Secure signup and login flow with hashed password storage (SHA-256).
- **Comprehensive Analytics:** Automatically calculates user stats including:
  - Total Scans performed.
  - Average Prediction Confidence.
  - Weekly Scanning activity.
- **Persistent Scan History:** Saves every prediction (Weight, Confidence, Status) to a local SQLite database for long-term tracking.
- **Robust API Integration:** Backend key-fixing logic to ensure PyTorch model compatibility across different environments.
- **Modern UI/UX:** Neon-themed Flet interface with a dedicated History tab and real-time scan feedback.

## 🛠️ Tech Stack
- **Frontend:** [Flet](https://flet.dev/) (Flutter for Python)
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) & Uvicorn
- **ML Engine:** PyTorch (ResNet18)
- **Database:** SQLite3
- **Image Processing:** PIL (Pillow) & Torchvision

## 📁 Project Structure
- `main.py`: The frontend application, database management, and UI logic.
- `backend.py`: FastAPI server for model inference and image preprocessing.
- `AIModel_3.ipynb`: The research and training pipeline.
- `sheep_app.db`: SQLite database for user data and history.
- `requirements.txt`: List of all Python dependencies.

## ⚙️ Setup Instructions

### 1. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
python backend.py
2. Frontend Setup
In a separate terminal:

Bash
python main.py
📊 Prediction Logic
The model performs a multi-output regression to determine:

Total Weight (kg)

Lean Mass %

Fat Mass %

Bone Mass %

