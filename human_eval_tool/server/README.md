# Human Evaluation Tool Backend

This section details the setup and usage of the Flask backend for the Human Evaluation Tool.

## Prerequisites

Before setting up the backend, ensure that you have the following prerequisites installed:

- Python 3.9 or 3.10
- MongoDB
- Flask
- Celery
- Socket.IO
- JWT (JSON Web Tokens)
- Pydantic

## Installation

To install the required Python environment, execute the following command:

```
pip install -r ../requirements.txt
```

## Configuration

The application configuration relies on environment variables. Set up your configuration by creating a `.env` file in the project root directory with the following variables:


   - `SECRET_KEY`: Used for JWT token encryption.
   - `MONGO_URI`: The URI of your MongoDB database.
   - `TASK_PATH`: Represents the task for testers, defined in **human_eval_tool/server/config**. Follow the format in [./config/test_goals.json](./config/test_goals.json).

## Usage

To start the application, execute the following command in the project root directory (the same as this README.md file):

```bash
python app.py
```

Upon running this command, the application will become accessible at http://localhost:5000.

## API Endpoints

For detailed information about the backend endpoints, refer to the `view/authentication.py` file. The SocketIO methods are implemented in `service/socketio.py`. You can review and modify these files to adjust the methods as needed.


---