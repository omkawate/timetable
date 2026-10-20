"""Browser coverage using the official dataset in a disposable database."""
import os
from pathlib import Path
import shutil,socket,subprocess,sys,tempfile,time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]

def run():
 with socket.socket() as sock:
  sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 with tempfile.TemporaryDirectory() as folder:
  with open(Path(folder)/'server.log','w') as log:
   server=subprocess.Popen([sys.executable,'run.py','--port',str(port)],cwd=ROOT,env={**os.environ,'UNISCHED_DB':str(Path(folder)/'test.db')},stdout=log,stderr=log)
   try:
    base=f'http://127.0.0.1:{port}'
    for _ in range(100):
     try:
      with urlopen(base+'/api/health',timeout=1) as r: assert r.status==200
      break
     except OSError: time.sleep(.1)
    with sync_playwright() as p:
     browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium'))
     page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     page.goto(base);expect(page.locator('#main')).to_contain_text('Your supplied curriculum')
     before=page.request.get(base+'/api/config').json()
     page.goto(base+'/#tutorials');expect(page.locator('#main tbody tr')).to_have_count(9)
     expect(page.locator('#main tbody tr').first).to_contain_text('710')
     page.get_by_role('button',name='Edit tutorial',exact=True).first.click()
     expect(page.locator('#f-teacher_id')).not_to_have_value('')
     expect(page.locator('#f-tutorial_room_id option:checked')).to_contain_text('710')
     page.get_by_role('button',name='Cancel',exact=True).click()
     page.goto(base+'/#projects');expect(page.locator('#main tbody tr')).to_have_count(2)
     expect(page.locator('#main tbody tr').first).to_contain_text('Independent project · no teacher')
     page.get_by_role('button',name='Edit project',exact=True).first.click()
     expect(page.locator('#f-teacher_id')).to_have_value('');expect(page.locator('#f-project_room_id')).to_have_value('')
     page.get_by_role('button',name='Cancel',exact=True).click()
     page.goto(base+'/#setup');expect(page.locator('#main tbody tr')).to_have_count(191)
     page.goto(base+'/#generate');page.locator('[data-action="generate-division"]').first.click()
     expect(page.locator('#f-classroom_run_length')).to_have_value('2')
     page.locator('#f-start_time').select_option('10:00')
     expect(page.locator('#modal')).to_contain_text('two-hour duration')
     page.get_by_role('button',name='Generate timetable',exact=True).click()
     expect(page.locator('.timetable')).to_be_visible(timeout=90000)
     expect(page.locator('.timetable')).to_contain_text('10:00–11:00')
     expect(page.locator('.timetable')).to_contain_text('TUTORIAL')
     expect(page.locator('#main')).to_contain_text('Practical sessions 2 hour(s)')
     assert page.request.get(base+'/api/config').json()==before
     # Every stacked batch card must fit inside its table cell without overlap.
     assert page.locator('.session-stack.parallel').evaluate_all('''stacks=>stacks.every(s=>{const cards=[...s.querySelectorAll('.lesson')];return cards.every((c,i)=>!i||c.getBoundingClientRect().top>=cards[i-1].getBoundingClientRect().bottom-1)})''')
     for label in ('PDF','Excel'):
      with page.expect_download() as download: page.get_by_role('link',name=label,exact=True).click()
      assert Path(download.value.path()).stat().st_size>1000
     for view in ('classroom','lab'):
      page.get_by_role('button',name='By '+view,exact=True).click();expect(page.locator('.timetable')).to_be_visible()
     full=page.request.post(base+'/api/generations',data={'time_limit':5,'start_time':'09:00'},timeout=60000).json()
     assert full['result']['status']=='feasible'
     page.reload();page.goto(base+'/#timetables')
     page.get_by_role('button',name='By division',exact=True).click()
     page.locator('#semester-select').select_option('7')
     expect(page.locator('.timetable')).to_contain_text('Major Project I')
     page.get_by_role('button',name='Edit timetable manually',exact=True).click()
     expect(page.locator('#modal')).to_contain_text('Independent project')
     page.get_by_role('button',name='Cancel',exact=True).click()
     page.goto(base+'/#tutorials');page.get_by_role('button',name='Edit tutorial',exact=True).first.click()
     page.get_by_role('button',name='Save tutorial',exact=True).click();expect(page.locator('#modal')).not_to_be_visible()
     after=page.request.get(base+'/api/config').json()['configuration'];assert after['teachers']==before['configuration']['teachers'];assert after['subjects']==before['configuration']['subjects']
     assert after['offerings'][182]['teacher_id']==before['configuration']['offerings'][182]['teacher_id']
     assert not errors,errors
     browser.close();print('Official browser checks passed: navigation, unassigned projects, tutorials, 10:00 generation, two-hour labs, batch cards, exports and room views.')
   finally:
    server.terminate();server.wait(timeout=10)
if __name__=='__main__': run()
