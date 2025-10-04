# Monthly Metrics Automation Project

A modular Python automation framework for exporting Jira data and uploading to Google Sheets.

## Features

- **JumpCloud Authentication**: Secure login with MFA support
- **Jira Integration**: Execute JQL queries and export CSV reports
- **Google Sheets Integration**: Automatic CSV to Sheets conversion
- **Modular Architecture**: Easy to maintain and extend
- **Robust Error Handling**: Comprehensive logging and error management
- **Flexible Execution**: Run full workflow or individual components

## Project Structure

```
jira-automation/
├── main.py                 # Main orchestrator script
├── config/
│   └── settings.py         # Configuration management
├── src/
│   ├── auth/              # Authentication modules
│   ├── automation/        # Selenium automation utilities
│   ├── jira/             # Jira-specific operations
│   ├── google/           # Google Drive/Sheets services
│   └── utils/            # General utilities
├── tests/                # Unit tests
├── logs/                 # Application logs
├── downloads/            # Downloaded files
└── credentials/          # Google API credentials
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- Google Cloud Project with Drive/Sheets API enabled
- JumpCloud account with Jira access

### 2. Installation Options

#### Option A: Using Poetry (Recommended)
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

#### Option B: Using pip
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in your credentials
2. **Google Credentials**: Download `credentials.json` from Google Cloud Console to `credentials/` folder
3. **Folder Setup**: The script will create necessary folders automatically

### 4. Usage

#### Run Full Workflow
```bash
python main.py --mode full
```

#### Export from Jira Only
```bash
python main.py --mode export-only
```

#### Upload to Google Sheets Only
```bash
python main.py --mode upload-only --file path/to/your/file.csv
```

## Configuration Details

### Environment Variables (.env)

- `JC_USERNAME`: Your JumpCloud email
- `JC_PASSWORD`: Your JumpCloud password  
- `JIRA_SEARCH_URL`: Jira issues search URL
- `JQL_QUERY`: JQL query to execute
- `DRIVE_FOLDER_ID`: Google Drive folder ID for uploads

### Google Setup

1. Create a Google Cloud Project
2. Enable Google Drive API and Google Sheets API
3. Create OAuth 2.0 credentials
4. Download credentials as `credentials.json`
5. Place in `credentials/` folder

## Development Setup

### IDE Recommendations

1. **PyCharm Community Edition** (Recommended for Python development)
   - Excellent Python support
   - Built-in debugging and testing
   - Integrated Git support

2. **Visual Studio Code**
   - Lightweight and versatile
   - Great extension ecosystem
   - Python extension for development

### Running Tests

```bash
# Using pytest
pytest tests/

# With coverage
pytest tests/ --cov=src/
```

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/
```

## Architecture Overview

### Key Design Principles

1. **Separation of Concerns**: Each module handles specific functionality
2. **Dependency Injection**: Services are injected rather than hard-coded
3. **Error Handling**: Comprehensive error handling with logging
4. **Configuration Management**: Centralized configuration with validation
5. **Testability**: Modular design enables easy unit testing

### Module Responsibilities

- **config/**: Application configuration and environment management
- **auth/**: Authentication services (JumpCloud, MFA)
- **automation/**: Web automation utilities and WebDriver management
- **jira/**: Jira-specific operations and data export
- **google/**: Google Drive and Sheets integration
- **utils/**: File operations and general utilities

## Troubleshooting

### Common Issues

1. **WebDriver Issues**: Update Chrome or run `pip install --upgrade webdriver-manager`
2. **Google Auth Issues**: Ensure credentials.json is valid and APIs are enabled
3. **JumpCloud MFA**: Approve push notifications within the timeout period
4. **File Download Issues**: Check Chrome download settings and folder permissions

### Logging

Logs are stored in `logs/jira_automation.log` with detailed information about each step.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MetroPolice License.
