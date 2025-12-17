# Cohort-Based Membership System

## Overview

This feature replaces individual registration-date-based expiry calculations with fixed cohort expiry dates. Users are automatically assigned to cohorts based on their submission date.

## Key Features

- Automatic cohort assignment based on registration window
- Blocks submissions when no active cohort exists
- Tracks full membership history with renewals
- Automatically provisions user accounts when admin approves requests
- Allows users to renew memberships (submit multiple requests over time)

## Admin Setup

### 1. Seed Initial Cohorts

```bash
python manage.py seed_cohorts
```

This creates cohorts for 2025-2030 based on predefined data.

### 2. Manage Cohorts

Access Django Admin → Cohorts

- **Open Registration**: Select cohorts and use "Open registration" action
- **Close Registration**: Select cohorts and use "Close registration" action
- **View Details**: cohort_id, name, registration dates, expiry dates, active status

### 3. Approve Subscriber Requests

Access Django Admin → Subscriber Requests

When you approve a request (change status to "approved"):
- If email doesn't exist: Creates new User + UserProfile + CohortMembership, sends welcome email
- If email exists: Updates UserProfile + creates new CohortMembership, sends renewal email

### 4. View Membership History

Access Django Admin → Cohort Memberships

- View all memberships per user across different cohorts
- See active vs inactive memberships
- Track renewal history

## Testing Workflow

### Test 1: Submit Request During Open Registration

1. Ensure at least one cohort has `is_active=True` and registration window is open
2. Go to `/subscriber-request/`
3. Fill form and submit
4. Verify request created with correct cohort assignment

### Test 2: Block Submission Outside Registration Window

1. Close all cohort registrations (set `is_active=False`)
2. Go to `/subscriber-request/`
3. Verify form shows "registration closed" message

### Test 3: Automatic User Provisioning (New User)

1. Create a subscriber request via form
2. Go to Admin → Subscriber Requests
3. Change status to "approved" and save
4. Verify new User created in Admin → Users
5. Verify UserProfile updated with cohort and expiry
6. Verify CohortMembership created with `is_active=True`

### Test 4: Renewal (Existing User)

1. Use email from an existing approved request
2. Submit new request (should succeed since previous is approved, not pending)
3. Approve the new request
4. Verify old CohortMembership set to `is_active=False`
5. Verify new CohortMembership created with `is_active=True`
6. Verify UserProfile updated to new cohort and expiry

### Test 5: Prevent Duplicate Pending Requests

1. Submit a request with email@example.com
2. Try to submit another request with same email while first is pending
3. Verify form shows error: "You already have a pending subscription request..."

## Technical Details

### Models

- **Cohort**: Defines registration windows and expiry dates
- **CohortMembership**: Tracks membership history with is_active flag
- **SubscriberRequest**: Auto-assigns cohort on creation based on submission date
- **UserProfile**: References current_cohort for quick access

### Key Business Logic

- Expiry dates determined by cohort, not individual registration dates
- Only pending requests enforce unique email constraint
- Approved requests allow same email for renewals
- Signal-based automatic provisioning on approval

### Management Commands

- `seed_cohorts`: Creates initial cohorts from predefined data
- `check_expired_users`: Checks membership expiry (updated for cohorts)

## Notes

- Historical data migrated to HISTORICAL_N cohorts (inactive)
- Backward compatibility maintained for records without cohorts
- Email notifications sent automatically on approval
