import os
import json
import gspread
from settings import COLUMN_TYPE_THEME, COLUMN_TYPE_SUBTHEME
from oauth2client.service_account import ServiceAccountCredentials


class Sheet:
    scopes = ['https://spreadsheets.google.com/feeds']
    sheets = dict()
    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def __init__(self):
        self.json_creds = os.getenv("GOOGLE_SHEETS_CREDS_JSON")
        self.creds_dict = json.loads(self.json_creds)
        self.creds_dict["private_key"] = self.creds_dict["private_key"].replace("\\\\n", "\n")
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.creds_dict, self.scopes)
        self.client = gspread.authorize(self.creds)

    def open_sheet(self, **kwargs):
        if not 'sheet_link' in kwargs:
            return False

        self.spreadsheet = self.client.open_by_url(kwargs['sheet_link'])
        return self

    def get_first_list(self, **kwargs):
        self.sheets['1'] = self.spreadsheet.sheet1
        records = self.sheets['1'].get_all_records()
        items = []
        help_items = []
        result = ''

        for record in records:
            if not 'column' in kwargs:
                for line in record:
                    if str(record[kwargs['column']]) != '':
                        items.append(str(record[line]))
                        result += str(record[line])
                    break
            else:
                if str(record[kwargs['column']]) != '':
                    items.append(str(record[kwargs['column']]))
                    result += str(record[kwargs['column']])

                if 'help_column' in kwargs:
                    column_name = kwargs['column'] + kwargs['help_column']
                    if str(record[column_name]) != '':
                        help_items.append(str(record[column_name]))

        if 'return_test' in kwargs:
            return result
        if 'return_items' in kwargs:
            if 'help_column' in kwargs:
                return {'items': items, 'help_items': help_items, }
            return items
        if 'return_records' in kwargs:
            return records

        return self.sheets['1']

    def set_first_list(self, **kwargs):
        if not 'column' in kwargs:
            return False

        col = self.spreadsheet.sheet1.col_count + 1
        self.spreadsheet.sheet1.add_cols(1)
        cell_list = self.spreadsheet.sheet1.range(1, col, len(kwargs['column']), col)

        i = 0
        for cell in cell_list:
            cell.value = str(kwargs['column'][i])
            i += 1

        self.spreadsheet.sheet1.update_cells(cell_list)


def get_column_type_options():
    return [COLUMN_TYPE_THEME, COLUMN_TYPE_SUBTHEME]
