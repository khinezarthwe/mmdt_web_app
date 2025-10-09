---
title: ReadMe

---

## User API for MMDT Telegram Bot
A simple REST API built with Python and Flask to manage and serve user-related data for a Telegram Bot integration.

This API provides a secure endpoint to fetch user profiles, which is protected by bearer token authentication.

## Features
- Get User by ID: Retrieve individual user profiles via a RESTful endpoint.
- Secure: Endpoints are protected using bearer token authentication to ensure only authorized clients (like the Telegram bot) can access the data.
- Lightweight: Built with Flask, a minimal and easy-to-understand web framework.

## Getting Started
Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites
Make sure you have the following software installed on your system:

- Python (Version 3.8 or higher is recommended)
- pip (Python Package Installer)
- git (Version Control System)

### Installation & Setup
1. Clone the Repository
Open your terminal and clone the project repository.

```
git clone [https://github.com/your-username/your-repository-name.git]
cd your-repository-name
```

2. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to isolate project dependencies.

```
# Create a virtual environment named 'venv'
python -m venv venv
```

- Activate On macOS/Linux:

```
source venv/bin/activate
```

- Activate On Windows:

```
venv\Scripts\activate
```

3. Install Dependencies
With your virtual environment activated, install the required Python packages from the requirements.txt file.

```
pip install -r requirements.txt
```

## Running the Server
Once the setup is complete, you can start the Flask development server.

```
python app.py
```

If the server starts successfully, you will see the following output in your terminal:

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on [http://12](http://12)-7.0.0.1:5000
```

## API Endpoints
The following section details the available API endpoints.

### Get User by ID
Retrieves the information for a single user specified by their ID.

- Endpoint: `GET /api/users/<user_id>`
- Description: Fetches the data for a user matching the provided `user_id` and returns it in JSON format.
- Authentication: Required (Bearer Token).
- Headers:
    - Authorization: Bearer <YOUR_API_KEY>

- URL Parameters:

 `user_id` (integer, required): The unique identifier of the user you want to retrieve.

- Example Request (curl):

```
curl -X GET -H "Authorization: Bearer MMDT-SECRET-TELEGRAM-BOT-KEY" [http://127.0.0.1:5000/api/users/2](http://127.0.0.1:5000/api/users/2)
```

- Success Response (200 OK):
If the user is found, the API returns their data as follows.

```
{
  "email": "mama@mmdt.com",
  "name": "Ma Ma",
  "registered_date": "2025-10-03"
}
```

- Error Responses:  

- `401 Unauthorized` : Returned if the `Authorization` header is missing or the token is invalid.

```
{
  "description": "Unauthorized access. Invalid or missing token."
}
```

 - `404 Not Found` : Returned if no user matches the requested user_id.  

```
{
  "description": "User with ID 99 not found."
}
```

