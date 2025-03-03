from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from tracking.models import TimeEntry
from datetime import datetime
import csv
import xlsxwriter
from io import BytesIO


@login_required
def export_report(request):
    # Handle date range selection
    today = datetime.now().date()
    start_date = today.replace(day=1)

    if 'start_date' in request.GET and request.GET['start_date']:
        try:
            start_date = datetime.strptime(
                request.GET['start_date'], '%Y-%m-%d').date()
        except ValueError:
            pass

    end_date = today
    if 'end_date' in request.GET and request.GET['end_date']:
        try:
            end_date = datetime.strptime(
                request.GET['end_date'], '%Y-%m-%d').date()
        except ValueError:
            pass

    # Filter by client/project/user
    client_id = request.GET.get('client_id')
    project_id = request.GET.get('project_id')
    user_id = request.GET.get('user_id')  # Neuer User-Filter

    filters = Q(start_time__date__gte=start_date,
                start_time__date__lte=end_date)

    if client_id:
        filters &= Q(project__client_id=client_id)

    if project_id:
        filters &= Q(project_id=project_id)

    if user_id:
        filters &= Q(user_id=user_id)

    entries = TimeEntry.objects.filter(filters).order_by('start_time')

    format_type = request.GET.get('format', 'xlsx')

    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="time_report_{start_date}_to_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Datum', 'Mitarbeiter', 'Kunde', 'Projekt', 'Beschreibung',
                        'Beginn', 'Ende', 'Stunden (gerundet)', 'Fakturierte Stunden', 'Stundensatz', 'Betrag'])

        for entry in entries:
            writer.writerow([
                entry.start_time.strftime('%d.%m.%Y'),
                entry.user.get_full_name() or entry.user.username,
                entry.project.client.name,
                entry.project.name,
                entry.description or '',
                entry.start_time.strftime('%H:%M'),
                entry.end_time.strftime('%H:%M') if entry.end_time else '',
                entry.get_rounded_duration(),
                entry.factored_hours if entry.factored_hours is not None else '',  # Add factored hours
                entry.project.hourly_rate,
                entry.get_billable_amount(),
            ])

        return response

    elif format_type == 'xlsx':
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Add header
        headers = ['Datum', 'Mitarbeiter', 'Kunde', 'Projekt', 'Beschreibung',
                   'Beginn', 'Ende', 'Stunden (gerundet)', 'Fakturierte Stunden', 'Stundensatz', 'Betrag']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Add data
        for row, entry in enumerate(entries, 1):
            worksheet.write(row, 0, entry.start_time.strftime('%d.%m.%Y'))
            worksheet.write(row, 1, entry.user.get_full_name()
                            or entry.user.username)
            worksheet.write(row, 2, entry.project.client.name)
            worksheet.write(row, 3, entry.project.name)
            worksheet.write(row, 4, entry.description or '')
            worksheet.write(row, 5, entry.start_time.strftime('%H:%M'))
            worksheet.write(row, 6, entry.end_time.strftime(
                '%H:%M') if entry.end_time else '')
            worksheet.write(row, 7, entry.get_rounded_duration())
            # Add factored hours
            worksheet.write(row, 8, float(entry.factored_hours)
                            if entry.factored_hours is not None else '')
            worksheet.write(row, 9, float(entry.project.hourly_rate))
            worksheet.write(row, 10, float(entry.get_billable_amount()))

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="time_report_{start_date}_to_{end_date}.xlsx"'

        return response

    else:
        return HttpResponse("Unsupported format", status=400)
