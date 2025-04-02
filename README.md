# McDonald's Outlets Finder & Chatbot

A React-based web application that visualizes McDonald's outlet locations on a map using Leaflet and OpenStreetMap. It also includes a chatbot that provides information about the outlets using the Gemini API.


## 📌 Features

<img width="352" alt="Screenshot 2025-04-02 at 11 14 36 AM" src="https://github.com/user-attachments/assets/c4fb2e19-fc25-4c7b-87d1-5b9b72e57261" />


### 🗺️ **Map Visualization**
- Displays McDonald's outlets on an interactive map.
- Uses Leaflet.js with OpenStreetMap tiles.
- Highlights outlets within a 5km radius of each other.

<img width="352" alt="Screenshot 2025-04-02 at 11 15 56 AM" src="https://github.com/user-attachments/assets/9aa5fd23-5351-4cb9-bbe8-1a1f1cf2be7f" />

### 🤖 **Chatbot**
- Users can ask about McDonald's outlets using natural language.
- Integrates with the Gemini API to fetch responses.
- Formats and displays responses in an interactive chat window.

<img width="352" alt="Screenshot 2025-04-02 at 11 16 48 AM" src="https://github.com/user-attachments/assets/37f09662-5f75-42ae-8997-1167316464a5" />

### 🔌 **Backend API**
- Developed using Python & FastAPI.
- Scrapes McDonald's outlet data and serves it to the frontend.
- Handles chatbot queries via the `/chat/{query}` endpoint.

---

## 🚀 Installation & Setup

### 1️⃣ **Clone the Repository**
```bash
git clone https://github.com/Jung028/mindhive-assessment.git
cd mindhive-assessment

# 🛠️ Project Setup

## 2️⃣ Backend Setup (FastAPI)
Ensure you have Python 3 installed.

cd backend
pip install -r requirements.txt
uvicorn mcd_outlet_scraper:app --host 0.0.0.0 --port 8000 --reload
```

The backend will run on [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 3️⃣ Frontend Setup (React)
Ensure you have Node.js installed.

```bash
cd frontend
npm install
npm start
```
The frontend will run on [http://localhost:3000](http://localhost:3000)

## 🛠️ Technologies Used
### Frontend
- **React.js** ⚛️
- **Leaflet.js** (for map visualization) 🗺️
- **OpenStreetMap** (tile provider) 🌍

### Backend
- **FastAPI (Python)** ⚡
- **Gemini API** (for chatbot responses) 🤖
- **Web scraping** (for outlet data) 🔍

## 📖 Project Structure
```bash
mindhive-assessment/
│── backend/                 # FastAPI backend
│   ├── main.py              # API entry point
│   ├── mcd_outlets_scraper.py # Scraper & chatbot logic
│   ├── requirements.txt      # Dependencies
│── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── App.js            # Main app component
│   │   ├── styles/           # CSS styles
│── README.md                 # Project documentation
```

## 🔥 Usage Guide

### 🗺️ Using the Map
1. Open the app ([http://localhost:3000](http://localhost:3000)).
2. View McDonald's outlet locations.
3. Zoom in/out and click markers for details.

### 🤖 Using the Chatbot
1. Open the chatbot by clicking the 💬 icon.
2. Ask a question like:

```vbnet
Where is the nearest McDonald's in Kuala Lumpur?
```

The chatbot will respond with relevant information.

## 📌 Future Enhancements
- 🔄 Real-time location updates.
- 🌍 Search by user's geolocation.
- 📱 Mobile responsiveness improvements.

## 🤝 Contributing
Contributions are welcome! Feel free to fork, make changes, and submit a pull request. 🚀

## 📜 License
This project is licensed under the **MIT License**.

## 📩 Contact
For any issues, feel free to open an issue or contact the project owner.
