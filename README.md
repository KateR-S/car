# Attendance Tracking App

A Streamlit application for tracking employee attendance at practices (all-hands days) and touches (workshops).

## Features

- **Employee Management**: Add, edit, and delete employees with member status and resident type
- **Practice Management**: Schedule and manage practices with dates and locations
- **Touch Management**: Organize workshops with up to 12 bells (participant slots) and a conductor
- **Password Protection**: Single-user authentication to protect data
- **Data Persistence**: All data is saved locally and persists across sessions

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
streamlit run app.py
```

Default password: `admin123` (can be changed in `config.py`)

## Project Structure

```
car/
├── app.py                 # Main application entry point
├── config.py              # Configuration and constants
├── requirements.txt       # Python dependencies
├── data/
│   └── data.json         # Data storage (auto-created)
├── src/
│   ├── auth.py           # Authentication logic
│   ├── data_manager.py   # Data persistence utilities
│   ├── models.py         # Data models
│   └── pages/
│       ├── employees.py  # Employee management page
│       ├── practices.py  # Practice management page
│       └── touches.py    # Touch management page
└── README.md
```

## Terminology

- **Practice**: An all-hands day event
- **Touch**: A workshop within a practice (up to 8 per practice)
- **Bell**: A participant slot in a touch (12 slots per touch)
- **Conductor**: The facilitator of a touch (occupies one bell slot)
- **Method**: The name/title of a workshop

## Data Model

### Employee
- First Name
- Last Name
- Member (Yes/No)
- Resident (Enum: Local, Regional, National, International)

### Practice
- Date (DD-MM-YYYY)
- Location (Enum: Office A, Office B, Office C, Remote)

### Touch
- Practice (linked to a Practice)
- Method (Workshop name)
- Conductor (Employee)
- Bells 1-12 (Employee assignments)
