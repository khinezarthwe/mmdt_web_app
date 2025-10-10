# Myanmar Data Tech Team - Database Schema

## Mermaid ER Diagram

```mermaid
erDiagram
    %% Auth/User Models
    User {
        int id PK
        string username UK
        string email
        string password
        string first_name
        string last_name
        boolean is_staff
        boolean is_active
        boolean is_superuser
        datetime last_login
        datetime date_joined
    }

    UserProfile {
        int id PK
        boolean expired
        datetime expiry_date
        datetime created_at
        datetime updated_at
        int user_id FK
    }

    %% Blog App Models
    Post {
        int id PK
        string title UK
        string slug UK
        text content
        int status
        string image
        int view_count
        boolean subscribers_only
        datetime created_on
        datetime updated_on
        int author_id FK
    }

    Comment {
        int id PK
        string name
        string email
        text body
        boolean active
        datetime created_on
        int post_id FK
    }

    SubscriberRequest {
        int id PK
        string name
        string email UK
        string mmdt_email
        string country
        string city
        string job_title
        string telegram_username
        boolean free_waiver
        text message
        string status
        string plan
        datetime expiry_date
        datetime created_at
        datetime updated_at
    }

    %% Polls App Models
    ActiveGroup {
        int group_id PK
        string group_name
        boolean is_active
        boolean registration_required
        boolean is_results_released
    }

    PollQuestion {
        int id PK
        string question_text
        datetime pub_date
        boolean is_enabled
        string image
        int poll_group_id FK
    }

    PollChoice {
        int id PK
        string choice_text
        int votes
        int question_id FK
    }

    %% Survey App Models
    Survey {
        int id PK
        string title
        text description
        string slug UK
        datetime start_date
        datetime end_date
        boolean is_active
        boolean registration_required
        boolean is_result_released
    }

    UserSurveyResponse {
        int id PK
        string guest_id
        boolean is_draft
        datetime created_at
        datetime updated_at
        int user_id FK
        int survey_id FK
    }

    SurveyQuestion {
        int id PK
        string question_text
        datetime pub_date
        boolean is_enabled
        string question_type
        string chart_type
        boolean optional
        int survey_id FK
    }

    SurveyChoice {
        int id PK
        string choice_text
        int question_id FK
    }

    Response {
        int id PK
        text response_text
        int question_id FK
        int user_survey_response_id FK
    }

    ResponseChoice {
        int id PK
        int response_id FK
        int choice_id FK
    }

    %% Relationships
    User ||--|| UserProfile : "has"
    User ||--o{ Post : "authors"
    Post ||--o{ Comment : "has"
    
    ActiveGroup ||--o{ PollQuestion : "contains"
    PollQuestion ||--o{ PollChoice : "has"
    
    Survey ||--o{ SurveyQuestion : "contains"
    Survey ||--o{ UserSurveyResponse : "receives"
    User ||--o{ UserSurveyResponse : "submits"
    
    SurveyQuestion ||--o{ SurveyChoice : "has"
    SurveyQuestion ||--o{ Response : "receives"
    UserSurveyResponse ||--o{ Response : "contains"
    
    Response ||--o{ ResponseChoice : "has"
    SurveyChoice ||--o{ ResponseChoice : "selected_in"
```

## Model Descriptions

### Blog App

#### **Post**
- Blog posts with rich text content
- Can be marked as subscriber-only
- Tracks view counts
- Status: Draft (0) or Published (1)

#### **Comment**
- Comments on blog posts
- Requires moderation (active flag)
- Ordered by creation time

#### **SubscriberRequest**
- Subscription requests from users
- Includes contact information and Telegram username
- Plans: 6-month ($12) or Annual ($24)
- Status: pending, approved, rejected, or expired
- Automatic expiry date calculation

### Polls App

#### **ActiveGroup**
- Groups polls together
- Controls visibility and registration requirements
- Manages results release

#### **PollQuestion**
- Poll questions with optional images
- Belongs to an active group
- Can be enabled/disabled

#### **PollChoice**
- Choices for poll questions
- Tracks vote counts

### Survey App

#### **Survey**
- Survey containers with title and description
- Time-based activation (start/end dates)
- Optional registration requirement
- Results can be released when ready

#### **UserSurveyResponse**
- Links users (or guests) to survey submissions
- Supports draft mode
- Tracks creation and update times

#### **SurveyQuestion**
- Questions within surveys
- Multiple question types: Text, Multiple Choice, Checkbox, Long Text, Dropdown, Sliding Scale
- Optional chart visualization (Pie/Bar)
- Can be marked as optional

#### **SurveyChoice**
- Answer choices for multiple choice/checkbox questions

#### **Response**
- User's answer to a specific question
- Can be text or selected choices
- Links to UserSurveyResponse

#### **ResponseChoice**
- Junction table for many-to-many relationship
- Links responses to selected choices

## Key Features

- **Authentication**: Django's built-in User model with Allauth integration
- **Content Management**: Blog posts with comments
- **Subscription System**: Tracks subscriber requests with expiry dates
- **Polling System**: Create and manage polls with groups
- **Survey System**: Comprehensive survey creation with multiple question types
- **Guest Support**: Surveys can be taken by anonymous users
- **Draft System**: Save responses as drafts before submission
