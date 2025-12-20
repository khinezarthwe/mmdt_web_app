# Cohort-Based Membership System

## Overview

Replaces individual registration-date-based expiry calculations with fixed cohort expiry dates. Subscriber requests are automatically assigned to cohorts based on submission date during active registration windows.

## Key Features

- Automatic cohort assignment to SubscriberRequests based on registration window
- Blocks submissions when no active cohort exists
- Tracks membership history across cohorts with CohortMembership model
- Allows renewals (multiple requests from same email over time)
- Prevents duplicate pending requests from same email

## Admin Setup

### 1. Seed Initial Cohorts

```bash
python manage.py seed_cohorts
```

Creates cohorts for 2025-2030 based on predefined registration windows and expiry dates.

### 2. Manage Cohorts

Access: **Admin → Cohorts**

- Open/Close registration: Select cohorts and use bulk actions
- View cohort details: cohort_id, name, registration dates, expiry dates, active status

### 3. Review Subscriber Requests

Access: **Admin → Subscriber Requests**

- View submitted requests with assigned cohort
- Approve/reject requests by changing status
- Cohort is automatically assigned when request is submitted

### 4. Manage Cohort Memberships

Access: **Admin → Cohort Memberships**

- Manually create CohortMembership records to link users to cohorts
- Track membership history across renewals
- Set is_active flag for current membership

## Testing Workflow

### Test 1: Submit Request During Open Registration

1. Ensure at least one cohort has `is_active=True` and current date is within registration window
2. Go to `/subscriber-request/`
3. Fill form and submit
4. Verify in Admin: request created with correct cohort assignment

### Test 2: Block Submission Outside Registration Window

1. Close all cohort registrations (set `is_active=False`)
2. Go to `/subscriber-request/`
3. Verify page shows "registration closed" message

### Test 3: Prevent Duplicate Pending Requests

1. Submit request with test@example.com
2. Try to submit another request with same email while first is pending
3. Verify form shows error: "You already have a pending subscription request..."

### Test 4: Allow Renewals

1. Approve first request (change status to "approved")
2. Submit new request with same email
3. Verify submission succeeds (approved requests don't block renewals)

## Technical Details

### Models

- **Cohort**: Registration windows and expiry dates per cohort
- **CohortMembership**: Tracks user membership history with is_active flag
- **SubscriberRequest**: Auto-assigns cohort on creation based on submission date
- **UserProfile**: References current_cohort for quick access

### Key Business Logic

- Expiry dates from cohort (exp_date_6 or exp_date_12), not registration date
- Only pending requests enforce unique email constraint
- Approved/rejected requests allow same email (enables renewals)
- SubscriberRequest.save() assigns cohort if within active registration window

### Management Commands

- `seed_cohorts`: Creates initial cohorts from predefined data
- `check_expired_users`: Checks membership expiry (updated for cohorts)

## Historical Data Migration

- Existing SubscriberRequests migrated to HISTORICAL_N cohorts (inactive)
- Groups old requests by expiry date into historical cohorts
- Migration runs automatically during deployment
- Backward compatibility maintained for records without cohorts
