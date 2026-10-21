"""Independent checks for balanced practical days and edge tutorials."""
import math
from .resources import affected_units, student_units

def audit_balance(config,entries):
    if not config.settings.balanced_days: return []
    errors=[];days=config.settings.days
    scheduled={e['group_id'] for e in entries}
    for group in config.groups:
        if group.id not in scheduled: continue
        ge=[e for e in entries if e['group_id']==group.id]
        for d in range(len(days)):
            daily=[e for e in ge if e['day']==d]
            if any(e['kind']=='lab' for e in daily) and not any(e['kind']=='lecture' for e in daily):
                errors.append(f'{group.id}, {days[d]}: practical day needs a lecture.')
        for unit in student_units(config,group):
            ids={o.id for o in config.offerings if unit in affected_units(config,o)}
            total=sum(o.labs for o in config.offerings if o.id in ids)
            for d in range(len(days)):
                daily=[e for e in ge if e['day']==d and e['offering_id'] in ids]
                count=sum(e['kind']=='lab' for e in daily)
                if count>math.ceil(total/len(days)) or (total>=len(days) and not count):
                    errors.append(f'{unit}, {days[d]}: practical sessions are not spread across the week.')
                used={q for e in daily for q in range(e['slot'],e['slot']+e['duration'])}
                for e in daily:
                    if e['kind']=='tutorial' and used and e['slot']!=min(used) and e['slot']+e['duration']-1!=max(used):
                        errors.append(f'{unit}, {days[d]}: tutorial must be at the start or end of the student day.')
    return errors
