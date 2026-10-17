"""Reproducible IT presentation data; never overwrites an existing database."""
from .domain import Configuration

CATALOG = {
3: [('Engineering Mathematics III','IT301','Dr. Anjali Deshmukh'),('Data Structures','IT302','Prof. Rahul Patil'),
    ('Database Management Systems','IT303','Prof. Sneha Joshi'),('Digital Logic & Architecture','IT304','Prof. Amit Shah'),
    ('Object-Oriented Programming','IT305','Prof. Pooja Kulkarni'),('Discrete Mathematics','IT306','Prof. Vikram More'),
    ('Web Technology','ITE301','Prof. Sanika Rane'),('Human Computer Interaction','ITE302','Prof. Omkar Kale')],
5: [('Operating Systems','IT501','Dr. Meera Nair'),('Computer Networks','IT502','Prof. Sandeep Jadhav'),
    ('Software Engineering','IT503','Prof. Neha Desai'),('Automata & Compiler Design','IT504','Prof. Kiran Rao'),
    ('Advanced Database Systems','IT505','Dr. Priya Menon'),('Information Security','IT506','Prof. Aditya Gokhale'),
    ('Artificial Intelligence','ITE501','Dr. Snehal Shinde'),('Cloud Fundamentals','ITE502','Prof. Akash Pawar')],
7: [('Machine Learning','IT701','Dr. Shreya Kulkarni'),('Big Data Analytics','IT702','Prof. Nikhil Sawant'),
    ('Cloud Computing','IT703','Prof. Kavita Iyer'),('Distributed Systems','IT704','Prof. Rohit Bhosale'),
    ('Cyber Security','IT705','Dr. Aditi Naik'),('DevOps & Software Architecture','IT706','Prof. Sameer Pawar'),
    ('Internet of Things','ITE701','Prof. Rutuja More'),('Blockchain Technology','ITE702','Dr. Harsh Mehta')]
}

def presentation_config():
    data={'departments':[{'id':'it','name':'Information Technology','code':'IT'}],
          'teachers':[],'subjects':[],'rooms':[],'groups':[],'offerings':[], 'elective_sets':[],
          'settings':{'start':'09:00','end':'17:45'}}
    for i in range(7):
        data['rooms'].append({'id':f'cr{i+1}','name':f'IT-{301+i}','kind':'classroom','capacity':70,
                             'department_id':'it','eligible_years':[]})
    for i in range(2):
        data['rooms'].append({'id':f'lab{i+1}','name':f'IT Shared Lab {i+1}','kind':'lab','capacity':70,
                             'department_id':'it','eligible_years':[]})
    for sem,subjects in CATALOG.items():
        data['elective_sets'].append({'id':f'es{sem}','name':f'Professional Electives – Semester {sem}',
                                      'code':f'PE-{sem}','department_id':'it','semester':sem})
        for index,(name,code,teacher) in enumerate(subjects):
            tid=f't{sem}_{index}'
            elective=index>=6
            lectures=4 if index<4 else 3 if index<6 else 2
            labs=1 if index in (1,2,4) else 0
            data['teachers'].append({'id':tid,'name':teacher,'department_id':'it','max_hours':20,
                'max_daily_slots':5,'arrival':'09:00','departure':'17:45','lab_eligible':True,
                'email':f'faculty{sem}{index}@example.edu','short_code':f'F{sem}{index}'})
            data['subjects'].append({'id':code,'name':name,'code':code,'department_id':'it','semester':sem,
                'elective':elective,'elective_set_id':f'es{sem}' if elective else None,
                'course_type':'mixed' if labs else 'theory','weekly_hours':lectures+labs*2})
            for div in 'ABC':
                data['offerings'].append({'id':f'{code}_{div}','group_id':f'it{sem}{div}','subject_id':code,
                    'teacher_id':tid,'lectures':lectures,'labs':labs,'lab_room_id':None})
        for div in 'ABC':
            data['groups'].append({'id':f'it{sem}{div}','department_id':'it','semester':sem,'division':div,
                                   'strength':60,'room_id':None})
    return Configuration(**data)
