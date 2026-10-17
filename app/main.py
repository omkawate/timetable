from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Literal
from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError, field_validator
from . import storage
from .domain import Configuration, COLLEGE, DAYS, PERIODS, parse_csv, configuration_csv
from .scheduler import generate, preflight
from .exports import pdf, excel

ROOT = Path(__file__).resolve().parent.parent
generation_lock = Lock()

@asynccontextmanager
async def lifespan(app):
    storage.initialize()
    if storage.get_config()['revision'] == 0:
        sample = parse_csv((ROOT / 'sample_data' / 'unisched_semesters_3_5_7.csv').read_bytes())
        try:
            storage.save_config(sample.model_dump(), 0)
        except storage.RevisionConflict:
            pass
    yield

app = FastAPI(title='UniSched API', version='1.0.0', lifespan=lifespan)

class ConfigUpdate(BaseModel):
    revision: int = Field(ge=0)
    configuration: Configuration

class GenerateRequest(BaseModel):
    name: str = Field(default='Odd semester timetable', min_length=1, max_length=80)
    time_limit: int = Field(default=20, ge=5, le=120)

    @field_validator('name')
    @classmethod
    def printable_name(cls, value):
        if any(ord(char) < 32 for char in value):
            raise ValueError('Timetable names cannot contain control characters or line breaks.')
        return value

@app.get('/api/health')
def health():
    with storage.connect() as db:
        db.execute('SELECT 1').fetchone()
    return {'status': 'ok', 'database': 'sqlite'}

@app.get('/api/meta')
def meta():
    return {'college': COLLEGE, 'days': DAYS, 'periods': PERIODS, 'recess': ['13:00','13:45']}

@app.get('/api/config')
def configuration():
    return storage.get_config()

@app.put('/api/config')
def save_configuration(payload: ConfigUpdate):
    try:
        revision = storage.save_config(payload.configuration.model_dump(), payload.revision)
    except storage.RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    return {'revision': revision, 'configuration': payload.configuration.model_dump()}

@app.get('/api/config.csv')
def export_configuration():
    body = configuration_csv(Configuration(**storage.get_config()['configuration']))
    return Response('\ufeff'+body, media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="unisched-academic-data.csv"'})

@app.get('/api/sample.csv')
def sample_csv():
    return FileResponse(ROOT/'sample_data'/'unisched_semesters_3_5_7.csv', media_type='text/csv', filename='unisched_semesters_3_5_7.csv')

@app.post('/api/import/preview')
async def import_preview(file: UploadFile = File(...)):
    try:
        config = parse_csv(await file.read(1_000_001))
    except (ValueError, ValidationError) as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await file.close()
    return {'configuration': config.model_dump(), 'counts': {k: len(v) for k,v in config.model_dump().items()},
            'issues': preflight(config)}

@app.get('/api/validate')
def validate_configuration():
    config = Configuration(**storage.get_config()['configuration'])
    return {'issues': preflight(config)}

@app.get('/api/generations')
def generation_list():
    return storage.generations()

@app.post('/api/generations')
def generate_timetable(payload: GenerateRequest):
    if not generation_lock.acquire(blocking=False):
        raise HTTPException(409, 'A timetable is already being generated. Please wait for it to finish.')
    try:
        current = storage.get_config()
        config = Configuration(**current['configuration'])
        result = generate(config, payload.time_limit)
        identifier = storage.save_generation(payload.name.strip() or 'Timetable', current['revision'], config.model_dump(), result)
        return storage.get_generation(identifier)
    finally:
        generation_lock.release()

@app.get('/api/generations/{identifier}')
def generation_detail(identifier: int):
    result = storage.get_generation(identifier)
    if result is None:
        raise HTTPException(404, 'Timetable not found.')
    return result

@app.get('/api/generations/{identifier}/export/{format}')
def export_generation(identifier: int, format: Literal['pdf','xlsx'], view: Literal['group','teacher']='group', target: str | None = Query(default=None, max_length=80)):
    record = generation_detail(identifier)
    if record['result']['status'] != 'feasible':
        raise HTTPException(409, 'Only a successfully generated timetable can be exported.')
    try:
        body = pdf(record, view, target) if format == 'pdf' else excel(record, view, target)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    mime = 'application/pdf' if format == 'pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return Response(body, media_type=mime, headers={'Content-Disposition': f'attachment; filename="UniSched-{view}-{identifier}.{format}"'})

app.mount('/static', StaticFiles(directory=ROOT/'static'), name='static')

@app.get('/', include_in_schema=False)
def index():
    return FileResponse(ROOT/'static'/'index.html')
