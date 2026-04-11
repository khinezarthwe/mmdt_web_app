# Users app management commands

Run from the Django project directory that contains `manage.py` (the `mmdt` folder):

```bash
cd mmdt
python manage.py <command> [options]
```

---

## 1. `check_expired_users`

**Purpose:** Walk every `UserProfile` that has an `expiry_date`. Mark profiles as expired (and deactivate the user) when `expiry_date` is in the past, or clear expired / reactivate when `expiry_date` is in the future.

**Does not** read Google Sheets. Uses only the database.

| Option | Description |
|--------|-------------|
| `--dry-run` | Print what would change; no saves. |

**Examples:**

```bash
python manage.py check_expired_users
python manage.py check_expired_users --dry-run
```

**Typical scheduling:** Daily (after expiry dates are accurate), e.g. cron at 07:00.

---

## 2. `sync_expiry_from_sheet`

**Purpose:** Pull membership expiry dates from the **members** Google Sheet and update `SubscriberRequest.expiry_date` and `UserProfile.expiry_date` when the sheet’s calendar `expired_date` differs from the DB.

**Sheet:** `GOOGLE_MEMBERS_SPREADSHEET_ID`, worksheet `GOOGLE_MEMBERS_WORKSHEET_NAME` (default `members`). Same OAuth + token files as other Sheets automation (`GOOGLE_OAUTH_CLIENT_SECRET_*`, `GOOGLE_TOKEN_FILE`).

**Columns used:** Only **`email`** and **`expired_date`** (header names are matched case-insensitively; `expiry_date` is accepted as an alias). Typical header row:

`id | full_name | email | cohort_id | first_joined_date | latest_renew_date | expired_date | status`

Other columns are ignored. Rows are skipped if `expired_date` is empty or unparsable.

**Behavior:**

- Updates only when the **calendar day** of `expired_date` changed (including when DB value was null).
- If `SubscriberRequest` was `expired` but the new expiry is in the future, status is set back to `approved` when the subscriber row is saved.
- `UserProfile.save()` may toggle `expired` / `is_active` from the new date.

| Option | Description |
|--------|-------------|
| `--dry-run` | Load the sheet and print would-be updates; no DB writes. |

**Examples:**

```bash
python manage.py sync_expiry_from_sheet
python manage.py sync_expiry_from_sheet --dry-run
```

**Typical scheduling:** Daily (e.g. 06:00), before `check_expired_users`, so flags match sheet-driven dates.

**Cron example:**

```cron
0 6 * * * cd /path/to/mmdt && /path/to/venv/bin/python manage.py sync_expiry_from_sheet >> /path/to/logs/sync_expiry.log 2>&1
```

---

## 3. `sync_approvals`

**Purpose:** For each **`SubscriberRequest` with `status='pending'`**, if that row’s email appears in the members sheet **Email** column, set `status` to **`approved`** and call **`save()`** on each instance so **`post_save`** runs (creates/links `User` and `UserProfile` via existing signals).

**Does not** iterate every sheet row looking for subscribers. Pending requests whose email is **not** on the sheet stay pending.

**Sheet:** Same spreadsheet and worksheet as `sync_expiry_from_sheet`. Only the **Email** column is read (duplicates in the sheet are de-duplicated).

**Guards:**

- Skips with an error message if another `User` has the same **username** as the subscriber email but a **different** email (avoids a bad `create_user` path).

**Transactions:** The approval loop runs inside a single `transaction.atomic()` block with `select_for_update()` on pending rows.

**Options:** None.

**Examples:**

```bash
python manage.py sync_approvals
```

**Typical scheduling:** As needed, or on a schedule after the sheet lists new members (often before or alongside expiry sync).

---

## Suggested daily order

1. `sync_approvals` — onboard pending members listed on the sheet.  
2. `sync_expiry_from_sheet` — refresh expiry dates from the sheet.  
3. `check_expired_users` — apply expire / reactivate from `UserProfile.expiry_date`.

Adjust times and frequency to match how often the sheet is updated.

---

## Google OAuth note

Sheet commands need a valid token (e.g. `google_token.json` on the server). The first authorization may require a browser; afterward refresh should work headlessly for cron. If the command fails with auth errors, renew the token using the same flow as your other Google integrations.
