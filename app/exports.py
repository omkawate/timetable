"""Horizontal timetable exports; scheduling and saved entries are not modified."""
import io
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html import escape
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from .domain import COLLEGE
from .presentation import layouts,calendar_rows

FONT_DIR=Path(__file__).resolve().parent.parent/'static'/'fonts'
pdfmetrics.registerFont(TTFont('TimetableSans',str(FONT_DIR/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('TimetableSans-Bold',str(FONT_DIR/'DejaVuSans-Bold.ttf')))


def workflow_label(generation):
    w=generation.get('workflow',{'state':'draft','locked':False})
    return w['state'].upper()+(' · LOCKED' if w['locked'] else '')


def matrix(layout):
    data=[['']*(len(layout['columns'])+1) for _ in range(layout['row_count'])]
    data[0]=['DAYS']+[('RECESS' if 'break' in c else 'P'+str(c['slot']+1))+'\n'+c['time'] for c in layout['columns']]
    for cell in layout['cells']:data[cell['row']][cell['col']]=cell['text']
    return data


def views(generation,view='group',target=None,batch=None):
    return [(x['title'],matrix(x),x['hours']) for x in layouts(generation,view,target,batch)]


def excel(generation,view='group',target=None,batch=None):
    wb=Workbook();wb.remove(wb.active)
    for index,layout in enumerate(layouts(generation,view,target,batch),1):
        sheet=wb.create_sheet(f'{index} '+{'group':'Division','teacher':'Professor','classroom':'Classroom','lab':'Lab'}[view]);n=len(layout['columns'])+1
        for row,text in [(1,COLLEGE),(2,layout['title']),(3,generation['name']+' · '+workflow_label(generation))]:
            sheet.merge_cells(start_row=row,start_column=1,end_row=row,end_column=n)
            cell=sheet.cell(row,1,text);cell.data_type='s';cell.font=Font(name='Calibri',size=16 if row==1 else 12,bold=True);cell.alignment=Alignment(horizontal='center',vertical='center');sheet.row_dimensions[row].height=25
        for r,values in enumerate(matrix(layout),5):
            sheet.row_dimensions[r].height=36 if r==5 else 32
            for c,text in enumerate(values,1):
                cell=sheet.cell(r,c,text);cell.data_type='s';cell.font=Font(name='Calibri',size=11,bold=r==5 or c==1)
                cell.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
                cell.border=Border(**{s:Side(style='thin',color='333333') for s in ['top','bottom','left','right']})
                if r==5:cell.fill=PatternFill('solid',fgColor='EDEDF5')
        for cell in layout['cells']:
            r=cell['row']+5;c=cell['col']+1
            if cell['rowspan']>1 or cell['colspan']>1:sheet.merge_cells(start_row=r,start_column=c,end_row=r+cell['rowspan']-1,end_column=c+cell['colspan']-1)
            if cell['kind']=='break':sheet.cell(r,c).fill=PatternFill('solid',fgColor='EEEAF8');sheet.cell(r,c).alignment=Alignment(horizontal='center',vertical='center',textRotation=90)
            if cell['rowspan']==1 and cell['text']:sheet.row_dimensions[r].height=max(sheet.row_dimensions[r].height,16*(cell['text'].count('\n')+1)+12)
        end=layout['row_count']+6
        legend_start=end
        bounds=[1,1+n//3,1+2*n//3,n+1]
        for i,legend in enumerate(layout['legends']):
            first,last=bounds[i],bounds[i+1]-1
            for offset,text in enumerate([legend['title']]+legend['items']):
                row=legend_start+offset
                sheet.merge_cells(start_row=row,start_column=first,end_row=row,end_column=last)
                cell=sheet.cell(row,first,text);cell.data_type='s';cell.font=Font(name='Calibri',bold=offset==0,size=11)
                cell.alignment=Alignment(wrap_text=True,vertical='center')
                cell.border=Border(bottom=Side(style='hair',color='AAAAAA'))
                if offset==0:cell.fill=PatternFill('solid',fgColor='EDEDF5')
                sheet.row_dimensions[row].height=max(sheet.row_dimensions[row].height or 0,32)
            end=max(end,legend_start+len(legend['items'])+1)
        sheet.column_dimensions['A'].width=9
        for i,col in enumerate(layout['columns'],2):sheet.column_dimensions[get_column_letter(i)].width=9 if 'break' in col else 19
        sheet.freeze_panes='B6';sheet.sheet_view.showGridLines=False
        sheet.page_setup.orientation='landscape';sheet.page_setup.paperSize=sheet.PAPERSIZE_A3
        sheet.page_setup.fitToWidth=1;sheet.page_setup.fitToHeight=0
        sheet.sheet_properties.pageSetUpPr.fitToPage=True;sheet.print_options.horizontalCentered=True
        sheet.print_title_rows='1:5';sheet.print_area=f'A1:{get_column_letter(n)}{end-1}'
    out=io.BytesIO();wb.save(out);return out.getvalue()


def pdf(generation,view='group',target=None,batch=None):
    out=io.BytesIO();doc=SimpleDocTemplate(out,pagesize=landscape(A3),leftMargin=25,rightMargin=25,topMargin=24,bottomMargin=24)
    heading=ParagraphStyle('heading',fontName='TimetableSans-Bold',fontSize=16,leading=20,alignment=TA_CENTER)
    normal=ParagraphStyle('normal',fontName='TimetableSans',fontSize=11,leading=14,alignment=TA_CENTER)
    cellstyle=ParagraphStyle('cell',parent=normal,fontSize=11,leading=14)
    legendstyle=ParagraphStyle('legend',fontName='TimetableSans',fontSize=10,leading=13)
    para=lambda text,style:Paragraph(escape(text).replace('\n','<br/>'),style)
    story=[]
    for index,layout in enumerate(layouts(generation,view,target,batch)):
        if index:story.append(PageBreak())
        story.extend([para(COLLEGE,heading),para(layout['title'],normal),para(generation['name']+' · '+workflow_label(generation),normal),Spacer(1,12)])
        weights=[.6]+[.75 if 'break' in c else 1 for c in layout['columns']];widths=[doc.width*w/sum(weights) for w in weights]
        grid=[[para(text,cellstyle) for text in row] for row in matrix(layout)]
        table=Table(grid,colWidths=widths,repeatRows=1,minRowHeights=[36]+[24]*(len(grid)-1))
        commands=[('GRID',(0,0),(-1,-1),.6,colors.HexColor('#333333')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDEDF5')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4)]
        for c in layout['cells']:
            if c['rowspan']>1 or c['colspan']>1:commands.append(('SPAN',(c['col'],c['row']),(c['col']+c['colspan']-1,c['row']+c['rowspan']-1)))
            if c['kind']=='break':commands.append(('BACKGROUND',(c['col'],c['row']),(c['col'],c['row']+c['rowspan']-1),colors.HexColor('#EEEAF8')))
        table.setStyle(TableStyle(commands));story.extend([table,Spacer(1,10)])
        legends=[]
        for l in layout['legends']:legends.append([para(l['title'],legendstyle)]+[para(x,legendstyle) for x in l['items']])
        legendrows=[[legends[c][r] if r<len(legends[c]) else '' for c in range(3)] for r in range(max(map(len,legends)))]
        legend=Table(legendrows,colWidths=[doc.width/3]*3,repeatRows=1)
        legend.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDEDF5')),('BOX',(0,0),(-1,-1),.5,colors.grey),('INNERGRID',(0,0),(-1,-1),.25,colors.lightgrey)]))
        story.extend([legend,Spacer(1,6),para('LAB: practical · TUT: tutorial · Blank cells: no assigned session. Each merged cell represents one complete session.',normal)])
    doc.build(story);return out.getvalue()
