import io
from html import escape
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from .domain import COLLEGE, DAYS, PERIODS

def views(generation, view='group', target=None):
    config = generation['config']
    key = 'groups' if view == 'group' else 'teachers'
    records = [item for item in config[key] if not target or item['id'] == target]
    if not records:
        raise ValueError('The selected division or professor is not in this saved timetable.')
    maps = {name: {x['id']: x for x in config[name]} for name in ('teachers', 'subjects', 'groups', 'rooms')}
    output = []
    for record in records:
        title = f"Semester {record['semester']} · Division {record['division']}" if view == 'group' else record['name']
        entries = [e for e in generation['result']['entries'] if e[view+'_id'] == record['id']]
        grid = [['Time', *DAYS]]
        for slot, (start, end) in enumerate(PERIODS):
            if slot == 4:
                grid.append(['13:00–13:45', *['RECESS'] * 5])
            row = [f'{start}–{end}']
            for day in range(5):
                entry = next((e for e in entries if e['day'] == day and e['slot'] <= slot < e['slot']+e['duration']), None)
                if not entry:
                    row.append('')
                    continue
                subject, group = maps['subjects'][entry['subject_id']], maps['groups'][entry['group_id']]
                type_label = 'LAB' if entry['kind'] == 'lab' else 'LECTURE'
                if subject['elective']:
                    type_label += ' · ELECTIVE'
                who = maps['teachers'][entry['teacher_id']]['name'] if view == 'group' else f"Sem {group['semester']} · Div {group['division']}"
                row.append(f"{subject['code']} · {type_label}\n{subject['name']}\n{who}\n{maps['rooms'][entry['room_id']]['name']}")
            grid.append(row)
        output.append((title, grid, sum(e['duration'] for e in entries)))
    return output

def excel(generation, view='group', target=None):
    workbook = Workbook()
    workbook.remove(workbook.active)
    for index, (title, grid, hours) in enumerate(views(generation, view, target), 1):
        sheet = workbook.create_sheet(f'{index} '+ ('Division' if view == 'group' else 'Professor'))
        for row, text in [(1, COLLEGE), (2, f'UniSched | {title}'), (3, f"{generation['name']} | {hours} teaching hours / week | Recess 13:00–13:45")]:
            sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
            cell = sheet.cell(row, 1, text)
            cell.data_type = 's'
            cell.font = Font(name='Calibri', size=14 if row == 1 else 11, bold=row != 3, color='252645')
            cell.alignment = Alignment(horizontal='center', vertical='center')
            sheet.row_dimensions[row].height = 25
        for r, values in enumerate(grid, 5):
            for c, value in enumerate(values, 1):
                cell = sheet.cell(r, c, value)
                cell.data_type = 's'
                cell.alignment = Alignment(wrap_text=True, vertical='center', horizontal='center')
                cell.font = Font(name='Calibri', size=10, color='FFFFFF' if r == 5 else '252645', bold=r == 5 or c == 1)
                cell.fill = PatternFill('solid', fgColor='5046D6' if r == 5 else 'F0EEFF' if r == 10 else 'F6F7FB')
                cell.border = Border(bottom=Side(style='thin', color='DFE2EB'))
            sheet.row_dimensions[r].height = 25 if r in (5,10) else 78
        sheet.column_dimensions['A'].width = 19
        for column in 'BCDEF':
            sheet.column_dimensions[column].width = 32
        sheet.freeze_panes = 'B6'
        sheet.sheet_view.showGridLines = False
        sheet.page_setup.orientation = 'landscape'
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A3
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 1
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.print_options.horizontalCentered = True
        sheet.print_area = 'A1:F14'
        sheet.oddFooter.center.text = 'UniSched · &P / &N'
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()

def pdf(generation, view='group', target=None):
    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=24, rightMargin=24,
                                 topMargin=20, bottomMargin=20, title='UniSched timetable', author=COLLEGE)
    heading = ParagraphStyle('heading', fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=colors.HexColor('#252645'), alignment=TA_CENTER)
    subheading = ParagraphStyle('subheading', fontName='Helvetica', fontSize=9, leading=13, alignment=TA_CENTER)
    cellstyle = ParagraphStyle('cell', fontName='Helvetica', fontSize=6.8, leading=8.2, alignment=TA_CENTER)
    headerstyle = ParagraphStyle('header', parent=cellstyle, fontName='Helvetica-Bold', textColor=colors.white)
    story = []
    for index, (title, grid, hours) in enumerate(views(generation, view, target)):
        if index:
            story.append(PageBreak())
        story += [Paragraph(escape(COLLEGE), heading), Spacer(1, 5),
                  Paragraph(escape(f"UniSched | {title} | {generation['name']}"), subheading),
                  Paragraph(escape(f'{hours} teaching hours/week · Monday–Friday · 09:00–17:45'), subheading), Spacer(1, 10)]
        table = Table([[Paragraph(escape(value).replace('\n', '<br/>'), headerstyle if r == 0 else cellstyle)
                        for value in row] for r, row in enumerate(grid)],
                       colWidths=[74]+[144]*5, rowHeights=[23]+[48]*4+[20]+[48]*4)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5046D6')),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F7F8FC')),
            ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#EDEBFF')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), .4, colors.HexColor('#DDE0E9')),
            ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)]))
        story += [table, Spacer(1, 7), Paragraph('Labs occupy two consecutive periods. Empty cells indicate no scheduled teaching. Recess: 13:00–13:45.', subheading)]
    document.build(story)
    return output.getvalue()
