# SGK Export Form Application

A Flask-based web application for handling export forms with PDF generation capabilities.

## Features

- Dynamic form with client-side validation
- SQLite database for data persistence
- PDF generation and preview functionality
- Print-friendly styling
- Mobile-responsive design

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- WeasyPrint system dependencies (see installation notes below)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sgk_export
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install WeasyPrint system dependencies:
   - On macOS: `brew install pango`
   - On Ubuntu/Debian: `sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0`
   - On Windows: Follow instructions at https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Fill out the export form with required information
2. Submit the form to generate a preview
3. From the preview page, you can:
   - Download the form as a PDF
   - Print the form directly
   - View all entered information

## Project Structure

```
sgk_export/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── exports.db         # SQLite database (created automatically)
└── templates/
    ├── form.html      # Form template
    └── preview.html   # Preview/PDF template
```

## Development

- The application uses Flask-SQLAlchemy for database operations
- WeasyPrint is used for PDF generation
- Bootstrap 5 for responsive styling
- jQuery for dynamic form behavior

## Security Notes

- Form inputs are sanitized both client-side and server-side
- SQLAlchemy ORM prevents SQL injection
- PDF generation is done server-side for security

## License

[Your License Here] 