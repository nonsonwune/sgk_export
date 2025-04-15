# Helper Scripts Documentation

This document describes the helper scripts available for managing and debugging the SGK Export application. These scripts are designed to simplify common development and administration tasks.

## Table of Contents

- [Overview](#overview)
- [Available Scripts](#available-scripts)
  - [check_superuser.py](#check_superuserpy)
  - [check_shipments.py](#check_shipmentspy)
- [Using Helper Scripts](#using-helper-scripts)
- [Creating New Helper Scripts](#creating-new-helper-scripts)

## Overview

Helper scripts are standalone Python files that perform specific administrative or debugging tasks outside the main application flow. They leverage the application's models and database but run as separate processes, making them ideal for:

- Performing one-off administrative tasks
- Debugging application state
- Testing specific features in isolation
- Bulk data operations
- System maintenance

## Available Scripts

### check_superuser.py

**Purpose:** Manage superuser permissions for user accounts in the system.

**Features:**
- Displays a table of all users in the system with their current permissions
- Allows toggling the superuser status for any user
- Provides immediate feedback on changes made

**Usage:**
```bash
python check_superuser.py
```

**Example output:**
```
Current Users:
==================================================
Username             Name                      Admin      Superuser 
--------------------------------------------------
admin                Administrator             True       False     
superuser            Super User                True       True      
nonso                Nonso Nwune               False      False     
ebele                Ebele Okoye               True       False     

Enter username to toggle superuser status (or press Enter to skip): nonso
Updated nonso: superuser status is now True
```

**When to use:**
- When you need to grant or revoke superuser privileges
- When troubleshooting permission issues
- When setting up new administrator accounts

### check_shipments.py

**Purpose:** Query and display shipment records for debugging and verification.

**Features:**
- Connects to the database using the application context
- Retrieves and displays shipment data with formatted output
- Useful for verifying data integrity and troubleshooting

**Usage:**
```bash
python check_shipments.py
```

**Example output:**
```
Shipment ID: 0c40be53-d796-4a70-867d-112945cded42, Status: delivered
Shipment ID: dfa662fd-a8cf-492b-8dc9-037a03b00cb8, Status: in_transit
Shipment ID: 3c90606e-aa4b-448d-8538-8da2f7743cbe, Status: in_transit
Shipment ID: 4bff8e7a-52b7-4e29-8f3f-3a68ff871d3f, Status: processing
Shipment ID: f921004c-7b6d-4233-9cea-956c73996322, Status: processing
```

**When to use:**
- When verifying shipment data
- When troubleshooting shipment-related issues
- When checking database contents without using the application UI

## Using Helper Scripts

To use any helper script:

1. Activate your virtual environment:
   ```bash
   source venv/bin/activate  # On Unix/macOS
   venv\Scripts\activate     # On Windows
   ```

2. Run the script using Python:
   ```bash
   python script_name.py
   ```

3. Follow any interactive prompts if the script requires input

Helper scripts use the same database connection as your main application, so changes made will be reflected in the application.

## Creating New Helper Scripts

To create a new helper script:

1. Start with the application context setup:
   ```python
   from app import create_app, db
   from app.models.[relevant_model] import [Model]

   app = create_app()

   def main():
       with app.app_context():
           # Your script logic here

   if __name__ == "__main__":
       main()
   ```

2. Add your specific functionality
3. Include clear user feedback and error handling
4. Document the script's purpose and usage in this document

When creating helper scripts, consider the following best practices:
- Always use the application context when interacting with models
- Provide clear user feedback for all operations
- Include confirmation for destructive operations
- Add error handling for database operations
- Document your script in this file for future reference

## Security Considerations

Helper scripts often have elevated privileges and can make direct database changes. Always follow these security practices:

- Don't commit scripts with hardcoded credentials
- Use input validation for all user inputs
- Create backups before running scripts that modify data
- Test scripts in development before using in production
- Restrict access to helper scripts in production environments 