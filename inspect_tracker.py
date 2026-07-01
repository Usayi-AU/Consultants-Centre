import os
import pandas as pd

path = r"c:\Users\Accounts\Music\Constultancy Centre\Q12026 SHarepoint Tracker.xlsx"
print('exists', os.path.exists(path))
if os.path.exists(path):
    xl = pd.ExcelFile(path)
    print('sheets', xl.sheet_names)
    for sheet in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        print('\nSHEET', sheet, 'ROWS', len(df), 'COLS', len(df.columns))
        print(df.head(10).to_string())
        print('COLUMNS', list(df.columns))
