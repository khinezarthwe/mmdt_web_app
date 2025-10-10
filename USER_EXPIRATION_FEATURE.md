# User Expiration Feature Documentation

## Overview

The User Expiration feature allows administrators to mark users as expired, which automatically deactivates their accounts.

## Features

### 1. **Automatic Expiration Based on Date**
When a user has an `expiry_date` set:
- If current date/time >= `expiry_date`, user is automatically marked as `expired=True`
- If `expiry_date` is empty or `None`, no automatic expiration occurs
- If `expiry_date` is in the future, user remains active

### 2. **Automatic User Deactivation**
When a user is marked as `expired` (manually or automatically), their account is automatically set to `is_active=False`, preventing them from logging in.

### 3. **Automatic User Reactivation**
When a user's `expired` status is removed or their `expiry_date` is extended to the future, their account is automatically reactivated (`is_active=True`).

### 4. **Expiry Date Tracking**
Optional `expiry_date` field to track when a user's subscription expires.

## Database Schema

### UserProfile Model
```python
class UserProfile(models.Model):
    user = OneToOneField(User)  # One-to-one with Django User
    expired = BooleanField(default=False)  # Expiration flag
    expiry_date = DateTimeField(null=True, blank=True)  # Optional expiry date
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

## Admin Panel Usage

### Viewing User Expiration Status

1. **In User List View**:
   - Go to: Admin → Users
   - See the **"Expired Status"** column showing:
     - ✓ Expired (red)
     - ✗ Active (green)

2. **Filtering Users**:
   - Use the right sidebar filter: **"Profile__expired"**
   - Filter by: Yes (expired) or No (active)

### Managing Individual Users

1. **Edit a User**:
   - Click on any user in the list
   - Scroll down to the **"PROFILE"** section
   - Check/uncheck the **"Expired"** checkbox
   - Optionally set an **"Expiry date"**
   - Click **"Save"**

2. **Automatic Behavior**:
   - ✅ Checking "Expired" → User is deactivated (`is_active=False`)
   - ✅ Unchecking "Expired" → User is reactivated (`is_active=True`)

### Bulk Actions

Select multiple users and use the action dropdown:

#### **"Mark selected users as expired"**
- Marks all selected users as expired
- Automatically deactivates them
- Shows confirmation message

#### **"Mark selected users as active (not expired)"**
- Removes expired status from selected users
- Automatically reactivates them
- Shows confirmation message

## Code Usage

### Check if a User is Expired

```python
from django.contrib.auth.models import User

user = User.objects.get(username='someuser')

if user.profile.expired:
    print("User is expired and cannot log in")
else:
    print("User is active")
```

### Mark a User as Expired

```python
from django.contrib.auth.models import User
from django.utils import timezone

user = User.objects.get(username='someuser')
user.profile.expired = True
user.profile.expiry_date = timezone.now()
user.profile.save()  # This automatically sets is_active=False

print(f"User active status: {user.is_active}")  # Will be False
```

### Reactivate an Expired User

```python
user = User.objects.get(username='someuser')
user.profile.expired = False
user.profile.save()  # This automatically sets is_active=True

print(f"User active status: {user.is_active}")  # Will be True
```

### Query Expired Users

```python
from django.contrib.auth.models import User

# Get all expired users
expired_users = User.objects.filter(profile__expired=True)

# Get all active (non-expired) users
active_users = User.objects.filter(profile__expired=False)

# Get users with expiry date in the past
from django.utils import timezone
expired_by_date = User.objects.filter(
    profile__expiry_date__lt=timezone.now()
)
```

## Automatic Profile Creation

### For New Users
When a new user is created, a `UserProfile` is automatically created via Django signals with:
- `expired=False`
- `expiry_date=None`

### For Existing Users
A data migration (`0002_create_profiles_for_existing_users.py`) creates profiles for all existing users.

## Integration with SubscriberRequest

You can sync the expiry status with `SubscriberRequest`:

```python
from blog.models import SubscriberRequest
from django.contrib.auth.models import User

# Example: Sync expiry from SubscriberRequest
subscriber = SubscriberRequest.objects.get(email='user@example.com')
try:
    user = User.objects.get(email=subscriber.email)
    user.profile.expiry_date = subscriber.expiry_date
    
    # Check if expired
    if subscriber.status == 'expired':
        user.profile.expired = True
    
    user.profile.save()  # Auto-updates is_active
except User.DoesNotExist:
    pass
```

## Testing

The feature includes comprehensive tests:

```bash
# Run all tests
python manage.py test

# Test the expiration logic
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.first()
>>> print(f"Before: is_active={user.is_active}, expired={user.profile.expired}")
>>> user.profile.expired = True
>>> user.profile.save()
>>> user.refresh_from_db()
>>> print(f"After: is_active={user.is_active}, expired={user.profile.expired}")
```

## Security Considerations

1. **Expired users cannot log in** - Django's authentication checks `is_active`
2. **Existing sessions remain valid** - Consider adding middleware to check expiration on each request
3. **Admin users can still access** - Staff users are not affected by expiration unless explicitly set

## Automatic Expiry Checking

### Management Command

A management command is provided to check and update all users:

```bash
# Check what would be expired (dry run)
python manage.py check_expired_users --dry-run

# Actually expire/reactivate users based on expiry_date
python manage.py check_expired_users
```

**When to run this command:**
- Daily via cron job or scheduled task
- After bulk-updating expiry dates
- As part of maintenance routines

**What it does:**
- Finds all users with `expiry_date` set
- Marks users as `expired=True` if `expiry_date <= now()`
- Marks users as `expired=False` if `expiry_date > now()` and they were previously expired
- Automatically updates `is_active` status

### Scheduled Task Example

**Linux/Mac (crontab):**
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/mmdt && python manage.py check_expired_users
```

**Windows (Task Scheduler):**
Create a scheduled task to run the command daily.

## Automatic Behavior on Save

When you save a UserProfile (manually in admin or programmatically):

1. **If expiry_date is set and in the past:**
   - `expired` → `True` (automatically)
   - `is_active` → `False` (automatically)

2. **If expiry_date is set and in the future:**
   - `expired` → `False` (if it was True)
   - `is_active` → `True` (automatically)

3. **If expiry_date is empty/None:**
   - No automatic changes to `expired` status
   - Manual control only

## Best Practices

1. **Set expiry_date** when creating subscriptions for automatic management
2. **Run check_expired_users daily** to keep status up-to-date
3. **Use bulk actions** for managing multiple users efficiently
4. **Monitor expired users** regularly using the admin filter
5. **Set expiry_date from SubscriberRequest** to keep them in sync

## Integration Recommendations

### With SubscriberRequest
Sync expiry dates when approving subscriptions:

```python
# In your approval workflow
subscriber = SubscriberRequest.objects.get(id=request_id)
user = User.objects.get(email=subscriber.email)
user.profile.expiry_date = subscriber.expiry_date
user.profile.save()  # Automatically sets expired status
```
