# coverages/services/export_service.py
def export_workbooks(orgs, fmt):
    for org in orgs:
        with open_workbook(org, fmt) as wb:
            for report in org.reports:
                with wb.sheet(report.name) as sheet:
                    for row in report.rows():
                        sheet.write(row)
