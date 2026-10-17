"""Exercise real website flows in Chromium against a disposable SQLite database."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)

def run():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix='unisched-ui-') as folder:
        environment = {**os.environ,'UNISCHED_DB':str(Path(folder)/'browser.db')}
        with open(ARTIFACTS/'browser-server.log','w') as log:
            server = subprocess.Popen([sys.executable,'run.py','--port',str(port)],cwd=ROOT,env=environment,stdout=log,stderr=log)
            try:
                base = f'http://127.0.0.1:{port}'
                for _ in range(100):
                    try:
                        with urlopen(base+'/api/health',timeout=1) as response:
                            assert response.status == 200
                        break
                    except OSError:
                        if server.poll() is not None:
                            raise RuntimeError('Browser test server exited. See artifacts/browser-server.log.')
                        time.sleep(.1)
                else:
                    raise RuntimeError('Browser test server did not become ready.')
                with sync_playwright() as p:
                    executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
                    browser = p.chromium.launch(headless=True,executable_path=executable)
                    page = browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
                    page.set_default_timeout(10000)
                    errors=[]
                    page.on('pageerror',lambda error:errors.append(str(error)))
                    page.goto(base)
                    expect(page.get_by_role('heading',name='A better week starts here.')).to_be_visible()
                    expect(page.locator('.stat-number').first).to_have_text('18')
                    page.screenshot(path=str(ARTIFACTS/'overview-desktop.png'),full_page=True)

                    page.get_by_role('link',name='Academic setup',exact=True).click()
                    page.get_by_role('tab',name='Teachers').click()
                    page.get_by_role('button',name='Add teacher',exact=True).click()
                    page.get_by_label('Teacher name',exact=True).fill('Prof. Browser Test')
                    page.get_by_label('Teaching hours per week (maximum)',exact=True).fill('16')
                    page.get_by_role('button',name='Save teacher',exact=True).click()
                    expect(page.locator('#modal')).not_to_be_visible()
                    page.get_by_label('Search teachers',exact=True).fill('Browser Test')
                    expect(page.locator('#setup-table tbody tr')).to_have_count(1)
                    page.get_by_role('button',name='Edit teacher',exact=True).click()
                    page.get_by_label('Leaving / departure time',exact=True).fill('16:45')
                    page.get_by_role('button',name='Save teacher',exact=True).click()
                    expect(page.locator('#setup-table')).to_contain_text('16:45')
                    page.get_by_role('button',name='Delete teacher',exact=True).click()
                    page.locator('#modal').get_by_role('button',name='Delete teacher',exact=True).click()
                    expect(page.locator('#setup-table')).to_contain_text('No matching teachers')

                    page.get_by_role('link',name='Import data',exact=True).click()
                    page.locator('#csv-file').set_input_files(str(ROOT/'sample_data'/'unisched_semesters_3_5_7.csv'))
                    expect(page.locator('#import-result')).to_contain_text('54 assignments')
                    page.screenshot(path=str(ARTIFACTS/'import-desktop.png'),full_page=True)
                    page.get_by_role('button',name='Replace academic data',exact=True).click()
                    expect(page.get_by_role('heading',name='Academic setup',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Check requirements',exact=True).click()
                    expect(page.locator('#validation-result')).to_contain_text('Basic workload and capacity checks passed')

                    page.get_by_role('link',name='Timetables',exact=False).first.click()
                    page.get_by_role('button',name='Generate timetable',exact=True).first.click()
                    page.get_by_label('Timetable name',exact=True).fill('Browser verified semester')
                    page.locator('#modal').get_by_role('button',name='Generate timetable',exact=True).click()
                    expect(page.locator('.timetable')).to_be_visible(timeout=35000)
                    expect(page.locator('.diagnostics')).to_contain_text('All constraints satisfied')
                    expect(page.locator('.lesson')).to_have_count(19)
                    page.screenshot(path=str(ARTIFACTS/'timetable-desktop.png'),full_page=True)

                    page.get_by_role('button',name='By professor',exact=True).click()
                    expect(page.locator('.timetable-label')).to_have_text('Dr. Anjali Deshmukh')
                    expect(page.locator('.lesson')).to_have_count(9)
                    expect(page.locator('.timetable td.empty')).to_have_count(31)
                    for text in page.locator('.lesson').all_text_contents():
                        assert 'CSC301' in text
                        assert 'Div ' in text
                    page.screenshot(path=str(ARTIFACTS/'professor-desktop.png'),full_page=True)
                    for name,filename in [('PDF','professor.pdf'),('Excel','professor.xlsx')]:
                        with page.expect_download() as download:
                            page.get_by_role('link',name=name,exact=True).click()
                        download.value.save_as(ARTIFACTS/filename)
                        assert (ARTIFACTS/filename).stat().st_size > 1000

                    page.get_by_role('link',name='Academic setup',exact=True).click()
                    page.get_by_role('tab',name='Teachers').click()
                    page.get_by_label('Search teachers',exact=True).fill('Anjali')
                    page.get_by_role('button',name='Edit teacher',exact=True).click()
                    page.get_by_label('Teaching hours per week (maximum)',exact=True).fill('1')
                    page.get_by_role('button',name='Save teacher',exact=True).click()
                    expect(page.locator('#modal')).not_to_be_visible()
                    page.get_by_role('link',name='Timetables',exact=False).first.click()
                    expect(page.locator('.info-banner.warning')).to_contain_text('Academic data has changed')
                    page.get_by_role('button',name='Generate timetable',exact=True).click()
                    page.locator('#modal').get_by_role('button',name='Generate timetable',exact=True).click()
                    expect(page.locator('.diagnostics')).to_contain_text('Generation not possible')
                    expect(page.locator('.diagnostics')).to_contain_text('9 assigned hours')
                    expect(page.locator('.diagnostics')).to_contain_text('Reassign at least 8 hours')
                    page.screenshot(path=str(ARTIFACTS/'conflict-desktop.png'),full_page=True)

                    page.emulate_media(reduced_motion='reduce')
                    page.set_viewport_size({'width':390,'height':844})
                    page.goto(base+'/#overview')
                    expect(page.get_by_role('heading',name='A better week starts here.')).to_be_visible()
                    page.wait_for_function("document.querySelector('#sidebar').getBoundingClientRect().right <= 0")
                    page.evaluate("document.querySelector('#toast').classList.remove('visible')")
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.screenshot(path=str(ARTIFACTS/'overview-mobile.png'),full_page=True)
                    page.get_by_role('button',name='Toggle navigation',exact=True).click()
                    page.get_by_role('link',name='Import data',exact=True).click()
                    expect(page.get_by_role('heading',name='Bring your semester into focus.')).to_be_visible()
                    expect(page.locator('#sidebar')).not_to_have_class('sidebar open')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.get_by_role('button',name='Toggle navigation',exact=True).click()
                    page.get_by_role('link',name='Timetables',exact=False).first.click()
                    page.locator('#generation-select').select_option(index=1)
                    expect(page.locator('.timetable')).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.screenshot(path=str(ARTIFACTS/'timetable-mobile.png'),full_page=True)
                    page.get_by_role('button',name='Toggle navigation',exact=True).click()
                    page.get_by_role('link',name='Import data',exact=True).click()
                    page.locator('#csv-file').set_input_files({'name':'invalid.csv','mimeType':'text/csv','buffer':b'bad,headers\n1,2'})
                    expect(page.locator('#import-result')).to_contain_text('headers must match')
                    assert errors == [], errors
                    browser.close()
                    print('Browser smoke passed: desktop/mobile navigation, CRUD, CSV preview/import/rejection, generation, professor filtering, downloads, snapshot warning, and actionable infeasibility. No JavaScript errors.')
            finally:
                server.terminate()
                server.wait(timeout=10)

if __name__ == '__main__':
    run()
