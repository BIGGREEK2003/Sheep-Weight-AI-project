# Sheep Weight & Carcass Composition Prediction API

This project provides an end-to-end solution for livestock management using Computer Vision. It features a deep learning model trained to predict a sheep's weight and carcass metrics (lean, fat, and bone mass) from images, served via a high-performance fast API and a modern mobile interface.

## 🚀 Features
- **AI Engine:** Fine-tuned ResNet18 model for multi-output regression.
- **FastAPI Backend:** Robust API handling image processing and model inference.
- **Flet Frontend:** A sleek, neon-themed user interface with real-time analysis and scan history.
- **Database Integration:** SQLite backend for user authentication and historical data tracking.
- **Carcass Analysis:** Provides percentage breakdowns of Lean, Fat, and Bone content.

## 🛠️ Project Structure
- `AIModel_3.ipynb`: Training notebook including data augmentation and model fine-tuning.
- `backend.py`: FastAPI server that loads the `.pth` model and provides the `/predict` endpoint.
- `main.py`: The Flet application for the end-user (UI/UX).
- `sheep_resnet18_finetuned.pth`: The trained PyTorch model weights.
- `sheep_app.db`: Local database for users and results history.

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/BIGGREEK2003/Sheep-Weight-AI-project.git](https://github.com/BIGGREEK2003/Sheep-Weight-AI-project.git)
cd Sheep-Weight-AI-project
2. Install Dependencies
It is recommended to use a virtual environment:

Bash
pip install torch torchvision fastapi uvicorn pillow numpy flet requests scikit-learn
3. Run the Backend
Start the API server first:

Bash
python backend.py
The API will run at http://127.0.0.1:8008.

4. Run the Frontend
In a new terminal, launch the application:

Bash
python main.py
📊 How it Works
Input: The user uploads or takes a photo of a sheep via the Flet app.

Processing: The image is resized to 224x224 and normalized.

Inference: The ResNet18 model predicts the weight and body composition.

Storage: Results are saved to the SQLite database for the user to view in their "History" tab.

🛡️ Security Note
This repository has been scrubbed of sensitive Hugging Face API tokens. If you are contributing to this project, please use a local .env file for your credentials.
