# Database Name: mywebapp_db

## Tables

1. **auth_group**
   - Columns:
     - id (Primary Key)
     - name (Unique)

2. **auth_group_permissions**
   - Columns:
     - id (Primary Key)
     - group_id (Foreign Key references auth_group(id))
     - permission_id (Foreign Key references auth_permission(id))

3. **auth_permission**
   - Columns:
     - id (Primary Key)
     - content_type_id
     - codename
     - name

4. **auth_user**
   - Columns:
     - id (Primary Key)
     - password
     - last_login
     - is_superuser
     - username (Unique)
     - last_name
     - email
     - is_staff
     - is_active
     - date_joined
     - first_name

5. **auth_user_groups**
   - Columns:
     - id (Primary Key)
     - user_id (Foreign Key references auth_user(id))
     - group_id (Foreign Key references auth_group(id))

6. **auth_user_user_permissions**
   - Columns:
     - id (Primary Key)
     - user_id (Foreign Key references auth_user(id))
     - permission_id (Foreign Key references auth_permission(id))

7. **blog_comment**
   - Columns:
     - id (Primary Key)
     - name
     - email
     - body
     - created_on
     - active
     - post_id (Foreign Key references blog_post(id))

8. **blog_post**
   - Columns:
     - id (Primary Key)
     - title (Unique)
     - slug (Unique)
     - updated_on
     - content
     - created_on
     - status
     - author_id (Foreign Key references auth_user(id))

9. **django_admin_log**
   - Columns:
     - id (Primary Key)
     - object_id
     - object_repr
     - action_flag
     - change_message
     - content_type_id (Foreign Key references django_content_type(id))
     - user_id (Foreign Key references auth_user(id))
     - action_time

10. **django_content_type**
    - Columns:
      - id (Primary Key)
      - app_label
      - model

11. **django_migrations**
    - Columns:
      - id (Primary Key)
      - app
      - name
      - applied

12. **django_session**
    - Columns:
      - session_key (Primary Key)
      - session_data
      - expire_date

13. **django_summernote_attachment**
    - Columns:
      - id (Primary Key)
      - name
      - file
      - uploaded

14. **polls_choice**
    - Columns:
      - id (Primary Key)
      - choice_text
      - votes
      - question_id (Foreign Key references polls_question(id))

15. **polls_question**
    - Columns:
      - id (Primary Key)
      - question_text
      - pub_date

16. **sqlite_sequence**
    - Columns:
      - name
      - seq
