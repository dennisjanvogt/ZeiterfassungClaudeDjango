from django.http import HttpResponse
import csv
import xlsxwriter
from io import BytesIO


def export_time_entries(entries, format_type='xlsx'):
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="time_entries.csv"'

        writer = csv.writer(response)
        writer.writerow(['Datum', 'Kunde', 'Projekt', 'Beschreibung',
                        'Beginn', 'Ende', 'Stunden (gerundet)', 'Stundensatz', 'Betrag'])

        for entry in entries:
            writer.writerow([
                entry.start_time.strftime('%d.%m.%Y'),
                entry.project.client.name,
                entry.project.name,
                entry.description or '',
                entry.start_time.strftime('%H:%M'),
                entry.end_time.strftime('%H:%M') if entry.end_time else '',
                entry.get_rounded_duration(),
                entry.project.hourly_rate,
                entry.get_billable_amount(),
            ])

        return response

    elif format_type == 'xlsx':
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Add header
        headers = ['Datum', 'Kunde', 'Projekt', 'Beschreibung', 'Beginn',
                   'Ende', 'Stunden (gerundet)', 'Stundensatz', 'Betrag']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Add data
        for row, entry in enumerate(entries, 1):
            worksheet.write(row, 0, entry.start_time.strftime('%d.%m.%Y'))
            worksheet.write(row, 1, entry.project.client.name)
            worksheet.write(row, 2, entry.project.name)
            worksheet.write(row, 3, entry.description or '')
            worksheet.write(row, 4, entry.start_time.strftime('%H:%M'))
            worksheet.write(row, 5, entry.end_time.strftime(
                '%H:%M') if entry.end_time else '')
            worksheet.write(row, 6, entry.get_rounded_duration())
            worksheet.write(row, 7, float(entry.project.hourly_rate))
            worksheet.write(row, 8, float(entry.get_billable_amount()))

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="time_entries.xlsx"'

        return response

    else:
        return HttpResponse("Unsupported format", status=400)
