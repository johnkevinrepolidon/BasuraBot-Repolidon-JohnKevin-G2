# BasuraBot: Garbage Schedule & Eco Tracker

A responsive Django web app that centralizes garbage collection schedules and barangay announcements for Cebu City residents. Built with **Django templates (full stack)** and **PostgreSQL / Supabase**.

## Features

### Project Development 1 - Account Feature
- Resident registration (name, email, mobile, barangay, password + confirmation) with validation, hashed passwords and success/error messages
- Login / logout (30-minute inactivity timeout), `@login_required` protection
- Role-based dashboards: **Resident** and **Barangay Staff**; a user cannot open another role's dashboard (403)
- Profile view/edit (own profile only) and password change
- Staff accounts can only be created by a logged-in staff user

### Project Development 2 - Core Feature: Collection Schedules & Announcements
The core of BasuraBot is publishing and viewing the garbage collection schedule (SDD features F-03, F-05, F-08).

| Role | What they can do |
|------|------------------|
| Barangay Staff | Create, view, edit and deactivate **collection schedules**; post, edit and delete **announcements** (own barangay only) |
| Resident | See upcoming pickups (computed next pickup date/time) and current, non-expired announcements of their own barangay |

Business rules enforced: BR-08 (staff only, own barangay), BR-09 (no duplicate route/day/time per barangay, UNIQUE constraint + form check), BR-10 (residents see only their barangay), BR-11 (expiry later than posted time, CHECK constraint + form check; expired announcements hidden).
Records are linked to users (`announcement.posted_by` -> users) and to barangays (`route_schedule.barangay`, `announcement.barangay`).

## Tech stack
Python 3.10+, Django 5.x, PostgreSQL or Supabase (no SQLite), python-dotenv.

## Setup
```bash
git clone <your-repo-url> && cd <repo-folder>
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

cp .env.example .env              # then edit .env with your database credentials
python manage.py makemigrations accounts schedules
python manage.py migrate
python manage.py seed_demo        # demo barangays, test accounts, sample data
python manage.py runserver
```
Open http://127.0.0.1:8000/

**Database:** create an empty PostgreSQL database named in `DB_NAME`, or use the connection details from Supabase (Project Settings > Database) and set `DB_SSLMODE=require`.

**Admin:** `python manage.py createsuperuser` (creates a STAFF-role account in the Mambaling barangay).

### Test accounts (created by `seed_demo`)
| Role | Email | Password |
|------|-------|----------|
| Staff (Mambaling) | staff@basurabot.test | Staff12345 |
| Staff (Labangon) | staff2@basurabot.test | Staff12345 |
| Resident (Mambaling) | resident@basurabot.test | Resident123 |
| Resident (Labangon) | resident2@basurabot.test | Resident123 |

### Run the tests
```bash
python manage.py test
```
(The PostgreSQL user needs permission to create a test database.)

## Project structure
```
basurabot/   settings, root urls
accounts/    Barangay + User models, registration, login, dashboards, profile
schedules/   RouteSchedule + Announcement models, staff CRUD, resident views
templates/   Django templates (shared form_page.html / confirm.html)
static/css/  styles
docs/        PD2 completion report PDF
```

## Git workflow (required for PD2)
- `main`: stable only, no direct commits. `develop`: integration branch. `feature/<name>`: one per feature. Do not delete merged feature branches.
```bash
git checkout -b develop main
git checkout -b feature/schedule-management develop
# ... commit small, clear changes ...
git push -u origin feature/schedule-management   # open a Pull Request into develop on GitHub
# repeat for feature/announcements, then open a PR from develop into main
```
Example commit messages: `Add RouteSchedule model and migration`, `Add schedule create form with duplicate check`, `Restrict staff portal to own barangay`, `Add announcement expiry validation`, `Update README with setup steps`.
