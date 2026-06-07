# Client Relations Dashboard

A Django-based live dashboard for client action items and completed items, built with Tailwind CSS styling.

## Setup

1. Activate the virtual environment:

   ```powershell
   cd "c:\Users\Accounts\Documents\Consultancy Site\Client Relations Dashboard"
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Apply migrations:

   ```powershell
   python manage.py migrate
   ```

4. Create the admin account:

   ```powershell
   python manage.py createadmin
   ```

   This creates a default admin user with username `admin` and password `30`.

5. Import the Excel workbook:

   ```powershell
   python manage.py import_excel --path "Action Items Dashboard 15.05.2026.xlsx"
   ```

6. Run the development server:

   ```powershell
   python manage.py runserver
   ```

## App pages

- `/` - Dashboard summary page
- `/action-items/` - All client action items and edit/delete controls
- `/client-hub/` - Grouped view per client with completed and ongoing counts
- `/client/<client_name>/` - Client detail view with completed and ongoing action items
- `/admin-activity/` - Admin activity log (admin only)

## Access control

- Admin users (`is_staff`) can edit or delete any action item and view activity history.
- Regular users can only edit action items where their username matches the item owner.

## Timezone

The Django project is set to Zimbabwe time (`Africa/Harare`).
