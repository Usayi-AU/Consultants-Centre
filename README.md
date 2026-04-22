# Operations Reporting Dashboard

## Setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `python manage.py migrate`.
4. Import the tracker data with `python manage.py import_tracker`.
5. Start the server with `python manage.py runserver`.

## Access Rules

- Enter `operations@int` to unlock the team dashboard and tracker.
- Enter `int@operationsADMIN` to unlock the admin dashboard and By Operations staff view.
- The By Operations staff view and edit form are admin-only.

## Branding

- Place the company logo at `/static/img/intellego-logo.png`.
- The logo is rendered in the main header, unlock page, and browser tab icon.

## Workbook Import

The importer reads the Excel workbook stored in the project root and maps the tracker rows into the database.

To import from a specific file path, run `python manage.py import_tracker --workbook "C:/path/to/file.xlsx"`.

## Deploy on Render

1. Commit and push this project to GitHub.
2. In Render, choose New + then Blueprint.
3. Select this repository. Render will detect `render.yaml` and create:
	- a web service (`operations-dashboard`)
	- a PostgreSQL database (`operations-dashboard-db`)
4. Deploy the blueprint.
5. After first deploy, open the web service Shell and run:
	- `python manage.py import_tracker`

### Local note after deployment changes

If you changed dependencies, run this before starting the local server:

- `.venv\\Scripts\\python.exe -m pip install -r requirements.txt`
