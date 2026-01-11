# ParkEasy - Modern Parking Management System

![ParkEasy Banner](https://img.shields.io/badge/ParkEasy-Modern%20Parking%20Solution-06b6d4?style=for-the-badge&logo=appveyor)

ParkEasy is a comprehensive, web-based Parking Management System designed to streamline the process of parking spot allocation and management. Built with **Flask** and styled with a futuristic **Cyber/Deep Space** aesthetic, it offers a seamless experience for both Administrators and Users.

## 🚀 Key Features

### 🌟 Immersive UI/UX
- **Deep Space Theme**: A visually stunning dark mode with deep navy backgrounds, cosmic gradients, and neon accents.
- **Glassmorphism**: Premium frosted glass effects on cards and modals.
- **Interactive Animations**: Powered by `AOS` (Animate On Scroll) and `Vanilla Tilt` for 3D hover effects.
- **Responsive Design**: Fully optimized for desktops, tablets, and mobile devices.

### 👤 For Users
- **Easy Registration & Login**: Secure authentication system.
- **Real-time Booking**: View available spots and book instantly.
- **Dashboard**: Track active reservations, view parking history, and check total spend.
- **Cost Calculation**: Automatic calculation of parking fees based on duration.

### 🛡️ For Administrators
- **Centralized Control**: Manage all parking lots and spots from a single dashboard.
- **Analytics**: Visual statistics for occupancy, revenue, and user activity.
- **Management**: Add, update, or remove parking locations.

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite (SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Libraries**:
  - `AOS.js` (Scroll Animations)
  - `Vanilla-tilt.js` (3D Interactions)
  - `Chart.js` (Data Visualization)

## 📦 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd vehicle
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    python3 app.py
    ```

5.  **Access the App**
    Open your browser and navigate to: `http://127.0.0.1:5000`

## 📂 Project Structure

```
vehicle/
├── app.py                 # Main Flask Application entry point
├── config.py              # Configuration settings
├── models.py              # Database models (User, ParkingLot, etc.)
├── requirements.txt       # Project dependencies
├── static/
│   ├── css/
│   │   └── styles.css     # Custom Cyber/Cool styles
│   └── js/                # (Optional custom scripts)
├── templates/             # HTML Templates (Jinja2)
│   ├── admin/             # Admin-specific pages
│   ├── user/              # User-specific pages
│   ├── base.html          # Base layout template
│   ├── index.html         # Landing page
│   ├── login.html         # Login page
│   └── register.html      # Registration page
└── parking_system.db      # SQLite Database file
```

## 🎨 Theme Details
The application uses a custom CSS implementation found in `static/css/styles.css`.
- **Primary Colors**: Neon Blue (`#3b82f6`), Cyan (`#06b6d4`), Slate (`#64748b`)
- **Dark Mode**: Deep Navy/Black (`#030712`) background with animated grid and starfield gradients.
- **Light Mode**: Clean Ice/Sky Blue theme with high-contrast elements.
