# Myanmar Data Tech Web App

## Introduction

Welcome to the Myanmar Data Tech web application at https://mmdt.istarvz.com/

This Django-based web application provides content management for the Myanmar Data Tech.

## Features

### 📝 Blog System
- **Content Management**: Create and manage blog posts with rich text editing
- **Subscriber-Only Content**: Restrict certain posts to subscribers only
- **Comments System**: Allow readers to comment on blog posts
- **Image Support**: Upload and display images in blog posts
- **View Tracking**: Track post view counts
- **Subscription Management**: Handle subscription requests with Telegram username support

### 👥 User Management
- **Cohort-Based Membership**: Organize subscribers into cohorts with fixed registration windows and expiry dates
- **User Expiration System**: Automatically expire and deactivate users based on expiry dates
- **Profile Management**: Extended user profiles with expiration tracking and cohort assignment
- **Bulk Actions**: Mark multiple users as expired or active
- **Automatic Deactivation**: Users are automatically deactivated when expired
- **Email-based Authentication**: Django Allauth integration with Google OAuth
- **Renewal System**: Users can request membership renewal with plan selection

### 🔌 REST API
- **JWT Authentication**: Secure token-based authentication for API access
- **User Lookup**: Query user details by email
- **Renewal Requests**: Submit renewal requests via API (for Telegram bot integration)
- **OpenAPI Documentation**: Interactive Swagger UI at `/api/docs/`


## Prerequisites for project setup

Before we get started, make sure you have the following installed on your computer:

- **Python 3.9+**: If you don't have Python installed, follow this [guide](https://kinsta.com/knowledgebase/install-python/) to install it.
- **Git**: If you don't have Git installed, follow the instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

## Project Setup

Let's set up the project step by step:

1. **Clone the Repository**: Download the project files by running this command: `git clone <repository_url>`

2. **Open the Project**: Use your preferred Integrated Development Environment (IDE) to open the project folder.

3. **Create a Virtual Environment** (Recommended): It's a good practice to isolate project dependencies. You can create a virtual environment by following [these instructions](https://docs.python.org/3/tutorial/venv.html).

4. **Install Project Dependencies**: Run the command `pip install -r requirements.txt` to install the necessary libraries. Install setuptools by running the command `pip install setuptools`.
   
5. **Environment Configuration**: Create a `.env` file under `mmdt-web-app/mmdt/.env` and add the following key:value pairs:
   ```
   # Django Configuration
   SECRET_KEY = 'your-secret-key-here'
   DEBUG = True  # Set to False for production
   
   # AWS S3 Configuration (Optional - for file storage)
   AWS_ACCESS_KEY_ID = 'your-aws-access-key'
   AWS_SECRET_ACCESS_KEY = 'your-aws-secret-key'
   AWS_STORAGE_BUCKET_NAME = 'your-s3-bucket-name'
   
   # Email Configuration (Required for user registration)
   EMAIL_HOST_PASSWORD = 'your-email-password'

   # Google API configuration (Drive / Sheets integration)
   GOOGLE_PARENT_FOLDER_ID = 'your-google-drive-parent-folder-id'
   GOOGLE_SPREADSHEET_ID = 'your-google-spreadsheet-id'
   GOOGLE_ADMIN_EMAIL = 'mmdt@istarvz.com'  # or another admin email
   GOOGLE_OAUTH_CLIENT_SECRET_FILENAME = 'client_secret_xxx.apps.googleusercontent.com.json'
   GOOGLE_TOKEN_FILENAME = 'google_token.json'
   ```
   

6. **Database Setup**:
   - Navigate to the project directory: `cd mmdt`
   - Run these commands to set up the database:
     ```
     python manage.py makemigrations
     python manage.py migrate
     ```

7. **Create an Admin User**: Use this command `python manage.py createsuperuser` to create an admin user for managing the application. You'll be prompted to enter a username, email, and password for the admin user.

8. **Run the Project**: Start the web application by running: `python manage.py runserver`

9. **Optional - Set Up Automatic User Expiration**:
   ```bash
   # Check expired users manually
   python manage.py check_expired_users --dry-run
   python manage.py check_expired_users
   
   # Or set up a cron job to run daily (Linux/Mac)
   0 2 * * * cd /path/to/mmdt && python manage.py check_expired_users
   ```

10. **Access the Application**:
You can now access the following URLs in your web browser:
- [http://127.0.0.1:8000/](http://127.0.0.1:8000/): Home Page/Blog Page 
- [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin): Admin Panel
- [http://127.0.0.1:8000/our_playground/](http://127.0.0.1:8000/our_playground/): AI Feedback Analyzer
- [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/): API Documentation (Swagger UI)

- [http://127.0.0.1:8000/polls/](http://127.0.0.1:8000/polls/): Polls System [draft]
- [http://127.0.0.1:8000/survey/](http://127.0.0.1:8000/survey/): Survey System [draft]
- [http://127.0.0.1:8000/surveys/](http://127.0.0.1:8000/surveys/): Advanced Survey Forms [draft]

## REST API

The application provides a REST API for external integrations (e.g., Telegram bot).

### API Documentation

Interactive API documentation is available at `/api/docs/` (Swagger UI).

### Authentication

All API endpoints (except token generation) require JWT authentication:

```bash
# 1. Obtain access token (admin users only)
curl -X POST http://127.0.0.1:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Response:
# {"access_token": "eyJ0eX...", "expires_in": 900, "token_type": "Bearer"}

# 2. Use token in subsequent requests
curl -X GET "http://127.0.0.1:8000/api/users?email=user@example.com" \
  -H "Authorization: Bearer eyJ0eX..."
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token` | Get JWT access token (admin only) |
| GET | `/api/users?email=` | Get user details by email |
| GET | `/api/users/telegram?telegram_name=` | Get user details by telegram username |
| POST | `/api/user/request_renew` | Submit renewal request |
| GET | `/api/docs/` | Swagger UI documentation |
| GET | `/api/schema/` | OpenAPI schema (JSON) |

### Renewal Request

Submit a membership renewal request:

```bash
curl -X POST http://127.0.0.1:8000/api/user/request_renew \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "telegram_name": "username",
    "plan": "6month"
  }'

# Response:
# {"status": "success", "message": "Renewal request received", "upload_url": "https://drive.google.com/..."}
```

**Required fields:**
- `email` - User's email address
- `telegram_name` - User's Telegram username
- `plan` - Either `6month` or `annual`

## Technology Stack

- **Backend**: Django 4.2.4
- **REST API**: Django REST Framework with JWT authentication
- **Database**: SQLite (development)
- **Frontend**: Bootstrap 4, HTML5, CSS3, JavaScript
- **Authentication**: Django Allauth, SimpleJWT
- **File Storage**: Local (development), AWS S3 (production)
- **Google Integration**: Drive API, Sheets API (gspread)
- **AI/ML**: Scikit-learn, NumPy
- **Forms**: Django Crispy Forms
- **Icons**: Bootstrap Icons

## Key Dependencies

- `Django==4.2.4` - Web framework
- `djangorestframework` - REST API framework
- `djangorestframework-simplejwt` - JWT authentication
- `django-allauth==0.63.6` - Authentication system
- `django-summernote==0.8.20.0` - Rich text editor
- `django-form-surveys==2.4.0` - Advanced survey forms
- `gspread` - Google Sheets integration
- `google-api-python-client` - Google Drive API
- `scikit-learn==1.2.2` - Machine learning library
- `boto3==1.28.44` - AWS SDK
- `Pillow==10.0.0` - Image processing
- `coverage==7.10.7` - Test coverage analysis

## Management Commands

The application includes several custom management commands:

### Check Expired Users
Automatically expire users based on their expiry dates:
```bash
python manage.py check_expired_users [--dry-run]
```

This command:
- Finds all users with `expiry_date` set
- Marks users as expired if their expiry date has passed
- Automatically deactivates expired users
- Reactivates users if their expiry date is extended

**Recommended**: Run this command daily via cron job for automatic user expiration management.

## Testing

This project includes comprehensive test coverage for the blog and polls functionality.

### Running Tests

1. **Run All Tests**:
   ```bash
   cd mmdt
   python manage.py test
   ```

2. **Run Tests with Verbosity**:
   ```bash
   python manage.py test --verbosity=2
   ```

3. **Run Specific App Tests**:
   ```bash
   # Blog tests only
   python manage.py test blog.tests
   
   # Polls tests only
   python manage.py test polls.tests
   ```

4. **Run Tests with Coverage**:
   ```bash
   # Install coverage if not already installed
   pip install coverage
   
   # Run tests with coverage
   coverage run --source='.' manage.py test
   
   # View coverage report
   coverage report
   
   # Generate HTML coverage report
   coverage html
   ```

### Test Coverage

**Blog App Tests (44 tests)**:
- **Model Tests**: Post, Comment, SubscriberRequest models
  - Creation, validation, default values
  - String representations
  - Ordering and relationships
  - Expiry date calculations
  - Telegram username field (optional)
  
- **Form Tests**: CommentForm, SubscriberRequestForm, FeedbackAnalyzerForm
  - Valid data handling
  - Invalid data and error messages
  - Duplicate email validation
  - Required field validation
  
- **View Tests**: PostListView, PostDetailView, SubscriberRequestView, PlayGroundView
  - GET and POST requests
  - Authentication and permissions
  - Subscriber-only content access
  - View count incrementation
  - Email sending functionality
  
- **URL Tests**: All URL patterns and routing
  
- **Integration Tests**: Complete workflows for comments and subscriber requests

**Polls App Tests (12 tests)**:
- **Model Tests**: Question model
  - `was_published_recently()` method
  - Date/time handling
  
- **View Tests**: Index view, All results view
  - Question display logic
  - Active group filtering
  - Staff-only access control
  - Pagination

### CI/CD Pipeline

This project uses GitHub Actions for continuous integration:

- **Automated Testing**: Tests run automatically on every pull request
- **Code Quality Checks**: Black formatting, isort, flake8 linting
- **Security Scanning**: Safety and Bandit checks
- **Coverage Reporting**: Codecov integration
- **Branch Protection**: PRs must pass all tests before merging

See `.github/workflows/test.yml` for the complete CI/CD configuration.

### Writing New Tests

When adding new features, please include tests:

```python
from django.test import TestCase
from .models import YourModel

class YourModelTest(TestCase):
    def setUp(self):
        """Set up test data."""
        # Create test objects here
        
    def test_your_feature(self):
        """Test your feature description."""
        # Your test assertions here
        self.assertEqual(expected, actual)
```

## User Expiration Feature

This application includes an automatic user expiration system. For complete documentation, see [USER_EXPIRATION_FEATURE.md](USER_EXPIRATION_FEATURE.md).

### Key Features:
- **Automatic Expiration**: Users are automatically expired when `expiry_date` is reached
- **Automatic Deactivation**: Expired users are automatically deactivated (`is_active=False`)
- **Automatic Reactivation**: Extending expiry date automatically reactivates users
- **Admin Integration**: Manage expiration status directly in Django admin
- **Bulk Actions**: Mark multiple users as expired or active at once
- **Management Command**: `python manage.py check_expired_users` for batch processing

### Quick Example:
```python
# In Django admin: Set a user's expiry date
user.profile.expiry_date = datetime(2025, 12, 31)
user.profile.save()
# If date is in past: expired=True, is_active=False (automatic)
# If date is in future: expired=False, is_active=True (automatic)
```

## Cohort-Based Membership System

The application uses a cohort-based system to manage subscriber memberships with fixed expiry dates.

### How It Works:

1. **Cohorts**: Groups of subscribers who register during the same period
   - Each cohort has a registration window (start and end dates)
   - Fixed expiry dates for 6-month and annual plans
   - Can be opened/closed for registration via admin

2. **Auto-Assignment**: When users submit subscription requests
   - System checks for active cohort with current date in registration window
   - Automatically assigns the user to that cohort
   - Blocks registration when no active cohort exists

3. **Simplified Workflow**: `Cohort → SubscriberRequest → User`
   - cohort_id stored in SubscriberRequest table
   - current_cohort stored in UserProfile table
   - No renewal system (to be added separately later)

### Setup:

Create cohorts manually via Django Admin:
- Navigate to **Admin → Cohorts**
- Add new cohort with registration window and expiry dates
- Mark as active to accept registrations

### Key Features:
- ✅ Fixed expiry dates per cohort (not based on individual registration date)
- ✅ Registration window control (open/close periods)
- ✅ Automatic cohort assignment on submission
- ✅ Unique email enforcement across all requests
- ✅ Registration closed page with next cohort information

## Database Schema

For a detailed database schema with Mermaid ER diagram, see [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

### Quick Overview

The application uses the following main models:

**Users App**:
- `UserProfile` - Extended user profiles with expiration tracking
  - `expired` - Boolean flag for user expiration status
  - `expiry_date` - Automatic expiration date checking
  - `current_cohort` - Reference to user's cohort
  - Automatic `is_active` status management
  - Auto-created for all users via Django signals

**Blog App**:
- `Post` - Blog posts with rich content
- `Comment` - Comments on posts
- `Cohort` - Membership cohorts with registration windows
  - cohort_id (PK), registration dates, expiry dates
  - Controls registration window availability
- `SubscriberRequest` - Subscription requests with cohort assignment
  - Plans: 6-month ($12) or Annual ($24)
  - Auto-assigned to active cohort on submission
  - Expiry date from cohort (not registration date)
  - Status tracking (pending, approved, rejected, expired)
  - Unique email enforcement

**Polls App**:
- `ActiveGroup` - Poll groups
- `Question` - Poll questions
- `Choice` - Poll answer choices

**Survey App**:
- `Survey` - Survey containers
- `Question` - Survey questions (multiple types)
- `Choice` - Answer choices
- `UserSurveyResponse` - User/guest responses
- `Response` - Individual question responses
- `ResponseChoice` - Selected choices

