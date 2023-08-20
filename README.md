# Myanmar Data Tech Team Web App

## Introduction

Welcome to the Myanmar Data Tech Team Web Application Project! 
Here, we'll explain the project and how to get started.

## Project Page

For more details and project tracking, visit our [Project Page](https://github.com/users/khinezarthwe/projects/1/views/1).

## Meet the Team

Meet our team members who have been working hard on this project:
- Htet Kay Khine
- Myat Po Po Aung
- Nang Seng Lean Pein
- Aye Mya Han
- Khin Kyaing Kyaing Thein

## Key Features

Our web application comes with some cool features:
- **Home Page**: A landing page for the Myanmar Data Tech Team.
- **Blog Pages**: Keep up with the team's latest blogs and updates.
- **Polls Application**: Participate in team surveys and polls. [Optional]
- **User Management**: Manage your account and preferences.

## Prerequisites

Before we get started, make sure you have the following installed on your computer:

- **Python**: If you don't have Python installed, follow this [guide](https://kinsta.com/knowledgebase/install-python/) to install it.
- **Git**: If you don't have Git installed, follow the instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

## Project Setup

Let's set up the project step by step:

1. **Clone the Repository**: Download the project files by running this command: `git clone <repository_url>`

2. **Open the Project**: Use your preferred Integrated Development Environment (IDE) to open the project folder.

3. **Create a Virtual Environment** (Recommended): It's a good practice to isolate project dependencies. You can create a virtual environment by following [these instructions](https://docs.python.org/3/tutorial/venv.html).

4. **Install Project Dependencies**: Run the command `pip install -r requirement.txt` to install the necessary libraries.

5. **Database Setup**:
   - Run these commands to set up the database:
     ```
     python manage.py makemigrations
     python manage.py migrate
     ```

6. **Create an Admin User**: Use this command `python manage.py createsuperuser` to create an admin user for managing the application: You'll be prompted to enter a username, email, and password for the admin user.

7. **Run the Project**: Start the web application by running: `python manage.py runserver`

8. **Access the Application**:
You can now access the following URLs in your web browser:
- [http://127.0.0.1:8000/](http://127.0.0.1:8000/): Home Page/Blog Page 
- [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin): Admin Panel
- [http://127.0.0.1:8000/polls](http://127.0.0.1:8000/polls): Polls Application [Optionals]
