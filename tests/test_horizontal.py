import sys,json,sqlite3,copy,io
from pathlib import Path
from app.domain import Configuration
from app.presentation import layouts
from app.exports import pdf,excel
from app.hints import reference_entries
from openpyxl import load_workbook

def test_horizontal_geometry_exports_and_immutability():
    c=sqlite3.connect('file:'+str(Path(__file__).parents[1]/'data/unisched.db')+'?mode=ro',uri=True)
    d=json.loads(c.execute('select body from configuration').fetchone()[0])
    for o in d['offerings']:
     if o['id'] in ['o'+str(i) for i in range(136,145)]:o['lab_room_type']='classroom'
    x=Configuration(**d);x.settings.start_at_opening=False;x.settings.balanced_days=True;x.settings.prefer_parallel_batches=True;x.settings.classroom_run_length=2;x.settings.combined_elective_students={'IS':60,'STQA':60}
    entries=reference_entries(x);assert entries
    record={'id':999,'name':'Horizontal layout verification','config':x.model_dump(),'result':{'status':'feasible','entries':entries},'workflow':{'state':'draft','locked':False}}
    original=copy.deepcopy(record)
    for view in ['group','teacher','classroom','lab']:
     ls=layouts(record,view)
     for layout in ls:
      seen=set()
      for cell in layout['cells']:
       cells={(r,c) for r in range(cell['row'],cell['row']+cell['rowspan']) for c in range(cell['col'],cell['col']+cell['colspan'])}
       assert not cells&seen,(view,layout['title'],cell)
       seen |= cells
       if cell['kind']=='lab':assert cell['colspan']==2
      assert len(seen)==(layout['row_count']-1)*(len(layout['columns'])+1)
     output=pdf(record,view);assert output[:4]==b'%PDF'
     book=load_workbook(io.BytesIO(excel(record,view)));assert len(book.worksheets)==len(ls)
     assert any(len(s.merged_cells.ranges)>3 for s in book)
     print(view,len(ls),'layouts and exports passed',flush=True)
    assert record==original
