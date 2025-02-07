# SGK Export Management System

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-latest-blue.svg)](https://www.postgresql.org/)
[![AppWrite](https://img.shields.io/badge/appwrite-1.4%2B-orange.svg)](https://appwrite.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A robust Flask-based web application for managing and generating export documentation with advanced user management, PDF generation capabilities, and secure data handling.

## 🚀 Features

### Core Functionality
- **Dynamic Export Form Management**
  - Interactive form with real-time validation
  - Customizable form fields and validation rules
  - PDF generation and preview capabilities
  - Print-friendly formatting

### User Management
- **Role-based Access Control**
  - Super User (highest privilege level)
    - Complete system administration
    - User and admin management
    - System configuration access
  - Admin role (intermediate privilege)
    - Export form management
    - Regular user management
    - Report generation
  - User role (basic privilege)
    - Form submission and viewing
    - Personal profile management
  - Secure authentication system
  - Password management functionality
  - User activity tracking

### Technical Features
- **Advanced Data Handling**
  - PostgreSQL database integration
  - AppWrite cloud storage integration
  - Secure data persistence
  - Backup and restore capabilities
  
- **Modern UI/UX**
  - Responsive design for all devices
  - Bootstrap 5 integration
  - Interactive form elements
  - Real-time validation feedback

## 📋 Prerequisites

### System Requirements
- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL 12 or higher
- Git

### System Dependencies
- **Database Setup**
  - PostgreSQL server running locally or remotely
  - PostgreSQL development headers (for psycopg2)
    ```bash
    # Ubuntu/Debian
    sudo apt-get install postgresql postgresql-contrib libpq-dev
    # macOS
    brew install postgresql
    ```

- **WeasyPrint Dependencies**
  - **macOS**: 
    ```bash
    brew install pango
    ```
  - **Ubuntu/Debian**: 
    ```bash
    sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
    ```
  - **Windows**: Follow the [WeasyPrint Windows Installation Guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)

## 🛠 Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd sgk_export
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```

   Configure the following variables in `.env`:
   ```ini
   # Flask Configuration
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secure-key-here

   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost/sgk_export_db

   # AppWrite Configuration
   APPWRITE_ENDPOINT=your-appwrite-endpoint
   APPWRITE_PROJECT_ID=your-project-id
   APPWRITE_BUCKET_ID=your-bucket-id
   APPWRITE_API_KEY=your-api-key
   ```

5. **Initialize PostgreSQL Database**
   ```bash
   # Create database
   createdb sgk_export_db
   
   # Run migrations
   flask db upgrade
   ```

## 🚦 Running the Application

1. **Start the Development Server**
   ```bash
   python app.py
   ```

2. **Access the Application**
   - Open your browser and navigate to: `http://localhost:5000`
   - Default admin credentials:
     - Username: `admin`
     - Password: `admin` (change on first login)

## 📁 Project Structure

```
sgk_export/
├── app.py                 # Main Flask application file
├── templates/            # HTML templates
│   ├── base.html        # Base template with common elements
│   ├── form.html        # Export form template
│   ├── preview.html     # PDF preview template
│   ├── login.html       # Authentication template
│   └── manage_*.html    # Admin management templates
├── static/              # Static assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Image assets
├── uploads/            # Upload directory for temporary files
├── instance/           # Instance-specific files
├── requirements.txt    # Python dependencies
└── .env               # Environment configuration
```

## 💻 Development

### Technology Stack
- **Backend**: Flask 2.0+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cloud Storage**: AppWrite
- **Frontend**: 
  - Bootstrap 5
  - jQuery
  - Custom JavaScript
- **PDF Generation**: WeasyPrint
- **Authentication**: Flask-Login

### Key Components
- Flask-SQLAlchemy for database operations
- AppWrite SDK for cloud storage
- WeasyPrint for PDF generation
- Bootstrap 5 for responsive design
- jQuery for dynamic form handling

## 🔒 Security Features

- **Authentication & Authorization**
  - Secure password hashing
  - Role-based access control
  - Session management
  
- **Data Protection**
  - Input sanitization
  - CSRF protection
  - SQL injection prevention
  - Secure file handling
  - Environment variable protection

## 🔄 Backup and Restore

The system includes automated backup functionality for both database and cloud storage:
```bash
# Create a database backup
pg_dump sgk_export_db > backup.sql

# Restore from backup
psql sgk_export_db < backup.sql
```

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and queries:
- Create an issue in the GitHub repository
- Contact the development team at [contact email]

## 🙏 Acknowledgments

- Flask and its extensions contributors
- PostgreSQL community
- AppWrite team
- Bootstrap team
- WeasyPrint developers
- All contributors to this project 