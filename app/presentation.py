"""Display-only timetable geometry shared by the browser, PDF and Excel."""
import re
from .domain import COLLEGE, Configuration
from .calendar import clock, minutes
from .resources import booking_key


def calendar_rows(settings):
    rows=[{'time':a+'–'+b,'slot':i} for i,(a,b) in enumerate(settings.periods())]
    rows += [{'time':b.start+'–'+clock(minutes(b.start)+b.duration),'break':b.name} for b in settings.breaks]
    return sorted(rows,key=lambda r:r['time'])


def aliases(records, teacher=False):
    result={};used=set()
    for item in records:
        name=item['name']
        words=re.findall(r'[A-Za-z0-9]+',name)
        if teacher: words=[w for w in words if w.lower() not in {'dr','mr','mrs','ms','mra','prof','professor'}]
        else: words=[w for w in words if w.lower() not in {'and','of','the','in','to','for'}]
        code=item.get('code','')
        short=code if not teacher and re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{0,9}',code) else ''.join(w[0] for w in words).upper() or 'NA'
        base=short;i=2
        while short in used:short=f'{base}{i}';i+=1
        used.add(short);result[item['id']]=short
    return result


def layouts(generation, view='group', target=None, batch=None):
    config=Configuration(**generation['config'])
    data=config.model_dump()
    settings=config.settings
    entries=generation['result']['entries']
    if batch:
        selected_batch=next((b for b in config.batches if b.id==batch),None)
        if view!='group' or not selected_batch or selected_batch.group_id!=target:
            raise ValueError('Choose a batch belonging to the selected division.')
        entries=[e for e in entries if not e.get('batch_id') or e['batch_id']==batch]
    scheduled={e['group_id'] for e in entries}
    if view not in ('group','teacher','classroom','lab'):
        raise ValueError('Choose a division, professor, classroom, or lab view.')
    room_view=view in ('classroom','lab')
    key='rooms' if room_view else 'groups' if view=='group' else 'teachers'
    records=[item for item in data[key] if (not target or item['id']==target) and (view!='group' or item['id'] in scheduled) and (not room_view or item['kind']==view)]
    if not records:
        raise ValueError('The selected division, professor, classroom, or lab is not in this saved timetable.')
    maps={name:{x['id']:x for x in data[name]} for name in ('teachers','subjects','groups','rooms','departments','batches')}
    output=[]
    for record in records:
        title=(f"{maps['departments'][record['department_id']]['code']} · Semester {record['semester']} · Division {record['division']}"
               if view=='group' else record['name'])
        if batch:
            title+=' · Batch '+selected_batch.name
        selected=[e for e in entries if e['room_id' if room_view else view+'_id']==record['id']]
        if view!='group':
            seen=set();unique=[];offerings={o.id:o for o in config.offerings}
            for e in selected:
                identity=(booking_key(config,offerings[e['offering_id']],e['kind']),e['day'],e['slot'],e['duration'],e['room_id'])
                if identity not in seen: unique.append(e);seen.add(identity)
            selected=unique
        subject_codes=aliases(data['subjects']);teacher_codes=aliases(data['teachers'],True)
        columns=calendar_rows(settings);slot_columns={r['slot']:i+1 for i,r in enumerate(columns) if 'slot' in r}
        cells=[];day_rows=[];row_index=1
        used_subjects=set();used_teachers=set();used_rooms=set()
        for day,day_name in enumerate(settings.days):
            events=sorted([e for e in selected if e['day']==day],key=lambda e:(e['slot'],-e['duration'],e.get('batch_id') or '',e['subject_id']))
            lanes=[];placed=[]
            for e in events:
                lane=next((i for i,end in enumerate(lanes) if end<=e['slot']),len(lanes))
                if lane==len(lanes):lanes.append(0)
                lanes[lane]=e['slot']+e['duration'];placed.append((e,lane))
            height=max(1,len(lanes));occupied=set()
            def add(row,col,text='',rs=1,cs=1,kind='empty',detail='',slot=None,duration=1):
                cells.append(dict(row=row,col=col,text=text,rowspan=rs,colspan=cs,kind=kind,detail=detail,day=day,slot=slot,duration=duration))
                occupied.update((r,c) for r in range(row,row+rs) for c in range(col,col+cs))
            add(row_index,0,day_name[:3].upper(),height,kind='day')
            for e,lane in placed:
                first=slot_columns[e['slot']];last=slot_columns[e['slot']+e['duration']-1]
                # Never join across recess, even for a malformed historical record.
                segments=[];start=first
                for col in range(first,last+1):
                    if 'break' in columns[col-1]:
                        if col>start:segments.append((start,col-start))
                        start=col+1
                if start<=last:segments.append((start,last-start+1))
                subject=maps['subjects'][e['subject_id']];teacher=maps['teachers'].get(e['teacher_id']);room=maps['rooms'].get(e['room_id'])
                batch_name=maps['batches'][e['batch_id']]['name'] if e.get('batch_id') else ''
                code=subject_codes[e['subject_id']]
                label=code+('-TUT' if e['kind']=='tutorial' else '')
                if batch_name:label+=' ('+batch_name+')'
                room_name=room['name'] if room else ''
                faculty=teacher_codes[e['teacher_id']] if teacher else ''
                text=' / '.join(v for v in [label,faculty,room_name] if v) if e['kind']!='lecture' else '\n'.join(v for v in [label,faculty,room_name] if v)
                if view!='group':
                    group=maps['groups'][e['group_id']];text+='\nSem '+str(group['semester'])+' · Div '+group['division']
                if e['kind']=='project' and not teacher:text='PROJECT'
                detail=' · '.join(v for v in [subject['name'],teacher['name'] if teacher else '',room_name,batch_name,settings.periods()[e['slot']][0]+'–'+settings.periods()[e['slot']+e['duration']-1][1]] if v)
                alone=not any(other is not e and other['slot']<e['slot']+e['duration'] and e['slot']<other['slot']+other['duration'] for other in events)
                if e['kind']=='lecture' and not alone:text=text.replace('\n',' / ')
                rs=height if alone else 1;rr=row_index if alone else row_index+lane
                for col,span in segments:add(rr,col,text,rs,span,e['kind'],detail,e['slot'],e['duration'])
                used_subjects.add(e['subject_id'])
                if teacher:used_teachers.add(teacher['id'])
                if room:used_rooms.add(room['id'])
            for col,column in enumerate(columns,1):
                if 'break' in column:
                    add(row_index,col,column['break'].upper(),height,kind='break');continue
                block=next((b for b in settings.blocked if b.day==day_name and b.slot==column['slot']),None)
                for rr in range(row_index,row_index+height):
                    if (rr,col) not in occupied:add(rr,col,block.reason if block else '',kind='blocked' if block else 'empty',slot=column['slot'])
            day_rows.append(dict(day=day_name,start=row_index,rows=height));row_index+=height
        # One recess column for the whole week, matching the printed college form.
        cells=[c for c in cells if c['kind']!='break' or c['row']==1]
        for cell in cells:
            if cell['kind']=='break':cell['rowspan']=row_index-1
        lab_subjects={e['subject_id'] for e in selected if e['kind']=='lab'}
        theory_subjects={e['subject_id'] for e in selected if e['kind']!='lab'}
        legends=[{'title':'Nomenclature of Subject','items':[subject_codes[s['id']]+' - '+s['name'] for s in data['subjects'] if s['id'] in theory_subjects]},
                 {'title':'Nomenclature of Subject Lab','items':[subject_codes[s['id']]+' - '+s['name'] for s in data['subjects'] if s['id'] in lab_subjects]},
                 {'title':'Location of Rooms / Labs','items':[r['name']+' - '+r['kind'].capitalize() for r in data['rooms'] if r['id'] in used_rooms]},
                 {'title':'Faculty Details','items':[teacher_codes[t['id']]+' - '+t['name'] for t in data['teachers'] if t['id'] in used_teachers]}]
        department=maps['departments'].get(record.get('department_id'),{})
        if not department and selected:
            departments={maps['groups'][e['group_id']]['department_id'] for e in selected}
            if len(departments)==1:department=maps['departments'][next(iter(departments))]
        semester=record.get('semester')
        year={1:'FIRST YEAR (FE)',2:'SECOND YEAR (SE)',3:'THIRD YEAR (TE)',4:'FINAL YEAR (BE)'}.get((semester+1)//2 if semester else 0,'')
        roman={1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',7:'VII',8:'VIII'}.get(semester,str(semester or ''))
        headers=[COLLEGE.upper(),('DEPARTMENT OF '+department.get('name','')).upper() if department else 'DEPARTMENT TIMETABLE',
                 ('DIVISION TIME TABLE' if view=='group' else view.upper()+' TIME TABLE')+' (Term - ______ · A.Y. __________)',
                 'Date of Commencement of Term: __________________']
        details=['YEAR: '+year,'SEMESTER - '+roman,'Division - '+record.get('division','')] if view=='group' else [title]
        output.append(dict(title=title,college=COLLEGE,columns=columns,cells=cells,row_count=row_index,days=day_rows,legends=legends,
                           headers=headers,details=details,signatures=['Prepared & Verified by\n\nTime Table Incharge'+(' ('+department['code']+')' if department else ''),'College Seal','Approved By\n\nHead of Department'],hours=sum(e['duration']*settings.period_minutes/60 for e in selected)))
    return output
