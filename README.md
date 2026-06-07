# IntelleGo Consultants Centre

Operations, Client Relations, Alternative Investments, and Business Development dashboards in one Django site.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `python manage.py migrate`.
4. Import all dashboard workbooks from `static/` with `python manage.py import_all_dashboards`.
5. Start the server with `python manage.py runserver`.

## Access Rules

- Enter `operations@int` to unlock the team dashboard and tracker.
- Enter `int@operationsADMIN` to unlock the admin dashboard and By Operations staff view.
- The By Operations staff view and edit form are admin-only.

## Branding

- Place the company logo at `/static/img/intellego-logo.png`.
- The logo is rendered in the main header, unlock page, and browser tab icon.

## Workbook Import

Place the latest dashboard files in `static/`:

| App | File pattern |
|-----|----------------|
| Operations | `Q1*Report Tracker*.xlsx` |
| Client Relations | `Action_Items_Dashboard*.xlsx` |
| Alternative Investments | `Alternative Investments*.docx` |
| Business Development | `Intellego_IPS_Business_Development_Tracker.xlsx` |

Import everything at once:

```powershell
python manage.py import_all_dashboards
```

Individual imports are also available: `import_tracker`, `import_excel`, `import_alt_investments`, and `import_bd_excel`.

## Client Relations — exit session

When unlocked, use **Exit** in the CRM header (all roles) or **Exit session** on the dashboard. This clears the `crm_access` session and returns you to the Consultants Centre hub.

## Deploy on Render + GitHub

See **[DEPLOY.md](DEPLOY.md)** for connecting Cursor to GitHub, pushing the repo, and deploying with Render Blueprint.

Quick summary:

1. Commit and push this project to GitHub.
2. In Render, choose **New** → **Blueprint**.
3. Select this repository. Render will detect `render.yaml` and create:
	- a web service (`consultants-centre`)
	- a PostgreSQL database (`operations-dashboard-db`)
4. Deploy the blueprint.

During each deploy, Render now runs this automatically before app start:

- `python manage.py migrate`
- `python manage.py seed_tracker_if_empty`

`seed_tracker_if_empty` only imports the workbook when there is no data yet, so existing admin updates are preserved.

### Local note after deployment changes

If you changed dependencies, run this before starting the local server:

- `.venv\\Scripts\\python.exe -m pip install -r requirements.txt`
