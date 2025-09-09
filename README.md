# Channel Management Service (`telegive-channel`)

This service is responsible for channel setup, validation, and permission management for the Telegive platform. It ensures that the bot has the necessary permissions to operate in a given Telegram channel.

## Core Features

- **Channel Setup**: Manual channel configuration and validation.
- **Permission Validation**: Verifies that the bot has the required permissions in channels.
- **Channel Information**: Fetches and stores channel details from the Telegram API.
- **Bot Status Verification**: Checks the bot's admin status in channels.
- **Permission Management**: Tracks and updates bot permissions.

## Technology Stack

- **Framework**: Flask (Python)
- **Database**: PostgreSQL (shared with other services)
- **External API**: Telegram Bot API
- **Validation**: Real-time channel and permission checking

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- `pip` for package installation

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/telegive-channel.git
   cd telegive-channel
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and provide the necessary values:
     - `DATABASE_URL`: Your PostgreSQL connection string.
     - `SECRET_KEY`: A secret key for Flask.
     - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
     - `TELEGRAM_BOT_ID`: Your Telegram bot's user ID.

### Running the Service

To run the service locally, use the following command:

```bash
flask run
```

The service will be available at `http://localhost:8002`.

### Running Tests

To run the test suite, use `pytest`:

```bash
pytest tests/
```

To get a coverage report:

```bash
pytest --cov=. tests/
```

## API Endpoints

For detailed API documentation, please refer to the `ChannelManagementService-CompleteDevelopmentSpecification.md` document.

- `POST /api/channels/setup`: Setup and validate a channel.
- `GET /api/channels/validate/{account_id}`: Validate an existing channel.
- `GET /api/channels/permissions/{account_id}`: Get bot permissions in a channel.
- `PUT /api/channels/update-permissions`: Update permission status.
- `GET /api/channels/info/{account_id}`: Get complete channel information.
- `POST /api/channels/revalidate/{account_id}`: Force revalidation of a channel.
- `GET /health`: Health check endpoint.

## Deployment

This service is designed for deployment on Railway. Follow the instructions in `ChannelManagementService-CompleteDevelopmentSpecification.md` for deployment.

## Project Structure

```
telegive-channel/
├── app.py                    # Main Flask application
├── models/                   # Database models
├── utils/                    # Core utilities and API integration
├── routes/                   # API routes
├── services/                 # Service layer classes
├── tasks/                    # Scheduled tasks
├── tests/                    # Test suite
├── config/                   # Configuration settings
├── requirements.txt
├── Procfile
├── railway.json
├── .env.example
├── .gitignore
└── README.md
```


