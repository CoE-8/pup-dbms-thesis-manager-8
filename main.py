import webapp2
import jinja2
import os
import logging
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb
import json
import csv
import re

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)

class User(ndb.Model):
    user_firstname = ndb.StringProperty(indexed=True)
    user_last_name = ndb.StringProperty(indexed=True)
    user_phone_number = ndb.IntegerProperty()
    user_email = ndb.StringProperty(indexed=True)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Thesis(ndb.Model):
    thesis_created_by = ndb.KeyProperty(kind='User')
    thesis_title = ndb.StringProperty(indexed=True)
    thesis_abstract = ndb.TextProperty()
    thesis_year = ndb.IntegerProperty()
    thesis_section = ndb.IntegerProperty()
    thesis_department_key = ndb.KeyProperty(kind='Department')
    thesis_student_keys = ndb.KeyProperty(kind='Student',repeated=True)
    thesis_adviser_key = ndb.KeyProperty(kind='Faculty')
    date = ndb.DateTimeProperty(auto_now_add=True)

class Student(ndb.Model):
    s_first_name = ndb.StringProperty(indexed=True,default='')
    s_middle_name = ndb.StringProperty(indexed=True,default='')
    s_last_name = ndb.StringProperty(indexed=True,default='')
    s_email = ndb.StringProperty(indexed=True)
    s_phone_num = ndb.StringProperty(indexed=True)
    s_student_num = ndb.StringProperty(indexed=True)
    s_birthdate = ndb.StringProperty()
    s_year_graduated = ndb.StringProperty(indexed=True)

class Faculty(ndb.Model):
    f_title = ndb.StringProperty(indexed=True)
    f_first_name = ndb.StringProperty(indexed=True,default='')
    f_middle_name = ndb.StringProperty(indexed=True)
    f_last_name = ndb.StringProperty(indexed=True,default='')
    f_email = ndb.StringProperty(indexed=True)
    f_phone_num = ndb.StringProperty(indexed=True)
    f_birthdate = ndb.StringProperty()

    @classmethod
    def get_by_key(cls, keyname):
        try:
            return ndb.Key(cls, keyname).get()
        except Exception:
            return None

class University(ndb.Model):
    u_name = ndb.StringProperty(indexed=True)
    u_address = ndb.StringProperty(indexed=True)
    u_initials = ndb.StringProperty(indexed=True)

class College(ndb.Model):
    c_name = ndb.StringProperty(indexed=True)
    c_university_key = ndb.KeyProperty(indexed=True)

class Department(ndb.Model):
    d_college_key = ndb.KeyProperty(indexed=True)
    d_name = ndb.StringProperty(indexed=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext
        }

        if user:
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');

class ThesisCreate(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('thesisForm.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');

class ImportCSV(webapp2.RequestHandler):
    def post(self):

        if self.request.get('csv_name'):
            if self.request.get('csv_name').find('.csv') > 0:
                csvfile = self.request.get('csv_name')
            else:
                csvfile = False;
                error = 'file type error'
        else:
            csvfile = False;
            error = 'please import a file!'

        if csvfile:
            f = csv.reader(open(csvfile , 'r'),skipinitialspace=True)
            counter = 1
            for row in f:
                # logging.info(counter)
                thesis = Thesis()
                th = Thesis.query(Thesis.thesis_title == row[4]).fetch()
                # know if thesis title already in database
                if not th:
                    if len(row[7]) > 2:
                        adviser_name = row[7] # 'Rodolfo Talan'
                        x = adviser_name.split(' ')
                        adv_fname = x[0]
                        adv_lname = x[1]
                        adviser_keyname = adviser_name.strip().replace(' ', '').lower()
                        adviser = Faculty.get_by_key(adviser_keyname)
                        if adviser is None:
                            adviser = Faculty(key=ndb.Key(Faculty, adviser_keyname), f_first_name=adv_fname, f_last_name=adv_lname)
                            thesis.thesis_adviser_key = adviser.put()
                        else:
                            thesis.thesis_adviser_key = adviser.key
                    else:
                        adv_fname = 'Anonymous'
                        adviser = Faculty(f_first_name=adv_fname, f_last_name=adv_lname)
                        thesis.thesis_adviser_key = adviser.put()
                    
                    for i in range(8,13):
                        stud = Student()
                        if row[i]:
                            stud_name = row[i].title().split(' ')
                            size = len(stud_name)
                            if size >= 1:
                                stud.s_first_name = stud_name[0]
                            if size >= 2:
                                stud.s_middle_name = stud_name[1]
                            if size >= 3:
                                stud.s_last_name = stud_name[2]
                            thesis.thesis_student_keys.append(stud.put())

                    university = University(u_name = row[0])
                    university.put()
                    college = College(c_name = row[1], c_university_key = university.key)
                    college.put()
                    department = Department(d_name = row[2], d_college_key = college.key)
                    thesis.thesis_department_key = department.put()

                    thesis.thesis_year = int(row[3])
                    thesis.thesis_title = row[4]
                    thesis.thesis_abstract = row[5]
                    thesis.thesis_section = int(row[6])

                    user = users.get_current_user()
                    user_key = ndb.Key('User',user.user_id())

                    thesis.thesis_created_by = user_key
                    thesis.put()

                    adv_fname = ''
                    adv_lname = ''
                    counter=counter+1
            self.response.write('CSV imported successfully')
        else:
            self.response.write(error)

class LoginPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template_data = {
            'login' : users.create_login_url(self.request.uri),
            'register' : users.create_login_url(self.request.uri)
        }
        if user:
            self.redirect('/register')
        else:
            template = JINJA_ENVIRONMENT.get_template('logReg.html')
            self.response.write(template.render(template_data))

class RegisterPage(webapp2.RequestHandler):
    def get(self):
        loginUser = users.get_current_user()

        if loginUser:
            user_key = ndb.Key('User',loginUser.user_id())
            user = user_key.get()
            if user:
                self.redirect('/')
            else:
                template = JINJA_ENVIRONMENT.get_template('regForm.html')
                logout_url = users.create_logout_url('/login')
                template_data = {
                    'logout_url' : logout_url
                }
                self.response.write(template.render(template_data))
                template_data 
        else:
            login_url = users.create_login_url('/register')
            self.redirect(login_url)

    def post(self):
        loginUser = users.get_current_user()
        fname = self.request.get('first_name').title()
        lname = self.request.get('last_name').title()
        pnum = int(self.request.get('phone_num'))
        email = loginUser.email()
        user_id = loginUser.user_id()

        u = User.query(User.user_firstname == fname).fetch()
        if u:
            for user in u:
                if user.user_last_name == lname:
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Name have already been taken',
                    }
                    self.response.out.write(json.dumps(response))
                    return

        user = User(id = user_id, user_email=email,user_firstname=fname,user_last_name = lname,user_phone_number = pnum)
        user.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))

class APIHandlerPage(webapp2.RequestHandler):
    def get(self):
        thesis_list = []
        if self.request.get('year').isdigit():
            filt_year = int(self.request.get('year'))
        else:
            filt_year = None
        filt_adviser = self.request.get('adviser')

        if filt_adviser:
            x = filt_adviser.split(' ')
            filt_adv_fname = x[0]
            f = Faculty.query(Faculty.f_first_name == filt_adv_fname).fetch()
            for faculty in f:
                filt_adv_key = faculty.key
        else:
            filt_adv_key = None

        filt_university = self.request.get('university')

        if filt_university:
            filt_univ = University.query(University.u_name == filt_university).get()
            filt_col = College.query(College.c_university_key == filt_univ.key).get()
            filt_dept = Department.query(Department.d_college_key == filt_col.key).get()
        else:
            filt_dept = None

        if filt_year and filt_university and filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_year == filt_year,Thesis.thesis_department_key == filt_dept.key,Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_year and filt_university:
            thesis = Thesis.query(Thesis.thesis_year == filt_year,Thesis.thesis_department_key == filt_dept.key).order(+Thesis.thesis_title).fetch()
        elif filt_year and filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_year == filt_year,Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_university and filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_department_key == filt_dept.key,Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_year:
            thesis = Thesis.query(Thesis.thesis_year == filt_year).order(+Thesis.thesis_title).fetch()
        elif filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_university:
            thesis = Thesis.query(Thesis.thesis_department_key == filt_dept.key).order(+Thesis.thesis_title).fetch()
        else:
            thesis = Thesis.query().order(+Thesis.thesis_title).fetch()

        for thes in thesis:
            d = ndb.Key('Department',thes.thesis_department_key.id())
            dept = d.get()
            dept_name = dept.d_name
            
            c = ndb.Key('College',dept.d_college_key.id())
            col = c.get()
            col_name = col.c_name

            u = ndb.Key('University',col.c_university_key.id())
            univ = u.get()
            univ_name = univ.u_name

            creator = thes.thesis_created_by.get()

            if thes.thesis_adviser_key:
                adv = thes.thesis_adviser_key.get()
                adv_fname = adv.f_first_name
                adv_lname = adv.f_last_name
            else:
                adv = None
                adv_fname = None
                adv_lname = None

            thesis_list.append({
                'self_id':thes.key.id(),
                'thesis_title':thes.thesis_title,
                'thesis_year':thes.thesis_year,
                'f_first_name':adv_fname,
                'f_last_name':adv_lname,
                'thesis_creator_fname':creator.user_firstname,
                'thesis_creator_lname':creator.user_last_name,
                })

        if thesis_list:
            response = {
                'status':'OK',
                'data':thesis_list
            }
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(response))
        else:
            response = {
                'status':'Error',
            }
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(response))

    def post(self):
        th = Thesis.query(Thesis.thesis_title == self.request.get('thesis_title')).fetch()
        thesis = Thesis()
        thesis.thesis_title = self.request.get('thesis_title')
        thesis.thesis_abstract = self.request.get('thesis_abstract')
        thesis.thesis_year = int(self.request.get('thesis_year'))
        thesis.thesis_section = int(self.request.get('thesis_section'))

        proponents = []
        if self.request.get('thesis_member1'):
            proponents.append(self.request.get('thesis_member1'))
        if self.request.get('thesis_member2'):
            proponents.append(self.request.get('thesis_member2'))
        if self.request.get('thesis_member3'):
            proponents.append(self.request.get('thesis_member3'))
        if self.request.get('thesis_membe4'):
            proponents.append(self.request.get('thesis_member4'))
        if self.request.get('thesis_member5'):
            proponents.append(self.request.get('thesis_member5'))

        adviser = self.request.get('thesis_adviser')
        univ = self.request.get('university')
        col = self.request.get('college')
        dept = self.request.get('department')

        if len(th) >= 1:
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'Cannot create thesis. Title may be already exist'
            }
            self.response.out.write(json.dumps(response))

        else:
            for i in range(0,len(proponents)):
                name = proponents[i].title().split(' ')
                size = len(name)
                s = Student()
                if size >= 1:
                    s.s_first_name = name[0]
                if size >= 2:
                    s.s_middle_name = name[1]
                if size >= 3:
                    s.s_last_name = name[2]
                thesis.thesis_student_keys.append(s.put())

            if len(adviser) > 2:
                adviser_name = adviser
                x = adviser_name.title().split(' ')
                sizex = len(x)
                if sizex >= 1:
                    adv_fname = x[0]
                else:
                    adv_fname = None

                if sizex >= 2:
                    adv_midname = x[1]
                else:
                    adv_midname = None

                if sizex >= 3:
                    adv_lname = x[2]
                else:
                    adv_lname = None

                adviser_keyname = adviser_name.strip().replace(' ', '').lower()
                adv = Faculty.get_by_key(adviser_keyname)
                if adv is None:
                    adv = Faculty(key=ndb.Key(Faculty, adviser_keyname), f_first_name=adv_fname, f_last_name=adv_lname, f_middle_name=adv_midname)
                    thesis.thesis_adviser_key = adv.put()
                else:
                    thesis.thesis_adviser_key = adv.key
            else:
                logging.info(len(adviser))
                adv_fname = 'Anonymous'
                adv_midname = None
                adv_lname = None
                adv = Faculty(f_first_name=adv_fname, f_last_name=adv_lname, f_middle_name=adv_midname)
                thesis.thesis_adviser_key = adv.put()


            university = University(u_name = univ)
            university.put()
            college = College(c_name = col, c_university_key = university.key)
            college.put()
            department = Department(d_name = dept, d_college_key = college.key)
            thesis.thesis_department_key = department.put()

            user = users.get_current_user()
            user_key = ndb.Key('User',user.user_id())

            thesis.thesis_created_by = user_key

            thesis.put()

            self.response.headers['Content-Type'] = 'application/json'
            response = {
            'status':'OK'
            }
            self.response.out.write(json.dumps(response))

class ThesisList(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        universities = []
        f = Faculty.query().order(+Faculty.f_last_name).fetch()
        u = University.query().order(+University.u_name).fetch()
        for univ in u:
            if univ.u_name not in universities:
                universities.append(univ.u_name)
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'faculty':f,
            'universities':universities
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('thesisList.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');
            
class CreateFaculty(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('facForm.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');
    def post(self):
        obj = json.loads(self.request.body)
        first_name = obj['faculty_data']['f_first_name']
        middle_name = obj['faculty_data']['f_middle_name']
        last_name = obj['faculty_data']['f_last_name']

        adviser_name = first_name + " " + middle_name + " " + last_name
        x = adviser_name.title().split()
        sizex = len(x)
        if sizex >= 1:
            adv_fname = x[0]
        else:
            adv_fname = None

        if sizex >= 2:
            adv_midname = x[1]
        else:
            adv_midname = None

        if sizex >= 3:
            adv_lname = x[2]
        else:
            adv_lname = None

        adviser_keyname = adviser_name.strip().replace(' ','').lower()
        adv = Faculty.get_by_key(adviser_keyname)
        if adv is None:
            adv = Faculty(key=ndb.Key(Faculty, adviser_keyname), f_first_name=adv_fname, f_last_name=adv_lname, f_middle_name=adv_midname,\
                f_email=obj['faculty_data']['f_email'],f_phone_num=obj['faculty_data']['f_phone_num'],f_birthdate=obj['faculty_data']['f_birthdate'],f_title=obj['faculty_data']['f_title'])
            adv.put()
            for i in range(len(obj['thesis'])):
                t = Thesis.query(Thesis.thesis_title == obj['thesis'][i]).fetch()
                if t[0].thesis_adviser_key is None:
                    t[0].thesis_adviser_key = adv.key
                    t[0].put()

                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'OK',
                    }
                    self.response.out.write(json.dumps(response))
                    return
                else:
                    adv.key.delete()
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Some thesis already have an adviser',
                    }
                    self.response.out.write(json.dumps(response))
                    return
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'OK',
            }
            self.response.out.write(json.dumps(response))
        else:
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'Faculty already exist!',
            }
            self.response.out.write(json.dumps(response))

class CreateStudent(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('studForm.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('../login');
    def post(self):
        obj = json.loads(self.request.body)
        name = obj['student_data']['s_first_name'] + " " + obj['student_data']['s_middle_name'] + " " + obj['student_data']['s_last_name']
        x = name.title().split()
        sizex = len(x)

        if sizex >= 1:
            first_name = x[0]
        else:
            first_name = None
        if sizex >= 2:
            middle_name = x[1]
        else:
            middle_name = None
        if sizex >= 3:
            last_name = x[2]
        else:
            last_name = None

        s = Student.query(Student.s_last_name == last_name).fetch()

        if s:
            for student in s:
                if student.s_first_name == first_name and student.s_middle_name == middle_name:
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Student already exist!',
                    }
                    self.response.out.write(json.dumps(response))
                    return
                else:
                    stud = Student()
                    stud.s_first_name = first_name
                    stud.s_middle_name = middle_name
                    stud.s_last_name = last_name

                    stud.s_email = obj['student_data']['s_email']
                    stud.s_phone_num = obj['student_data']['s_phone_num']
                    stud.s_student_num = obj['student_data']['s_student_num']
                    stud.s_birthdate = obj['student_data']['s_birthdate']
                    stud.s_year_graduated = obj['student_data']['s_year_graduated']
                    stud.put()
                    for i in range(len(obj['thesis'])):
                        t = Thesis.query(Thesis.thesis_title == obj['thesis'][i]).fetch()
                        if len(t[0].thesis_student_keys) < 5:
                            t[0].thesis_student_keys.append(stud.key)
                            t[0].put()
                            self.response.headers['Content-Type'] = 'application/json'
                            response = {
                                'status':'OK',
                            }
                            self.response.out.write(json.dumps(response))
                            return
                        else:
                            self.response.headers['Content-Type'] = 'application/json'
                            response = {
                                'status':'Maximum student in thesis',
                            }
                            self.response.out.write(json.dumps(response))
                            return
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'OK',
                    }
                    self.response.out.write(json.dumps(response))
        else:
            stud = Student()
            stud.s_first_name = first_name
            stud.s_middle_name = middle_name
            stud.s_last_name = last_name

            stud.s_email = obj['student_data']['s_email']
            stud.s_phone_num = obj['student_data']['s_phone_num']
            stud.s_student_num = obj['student_data']['s_student_num']
            stud.s_birthdate = obj['student_data']['s_birthdate']
            stud.s_year_graduated = obj['student_data']['s_year_graduated']
            stud.put()
            for i in range(len(obj['thesis'])):
                t = Thesis.query(Thesis.thesis_title == obj['thesis'][i]).fetch()
                if len(t[0].thesis_student_keys) < 5:
                    t[0].thesis_student_keys.append(stud.key)
                    t[0].put()
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'OK',
                    }
                    self.response.out.write(json.dumps(response))
                else:
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Maximum student in thesis',
                    }
                    self.response.out.write(json.dumps(response))
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'OK',
            }
            self.response.out.write(json.dumps(response))

class CreateUniversity(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('univForm.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');
    def post(self):
        name = self.request.get('university_name')
        lower = name.lower().replace(' ', '')
        u = University.query().order(+University.u_name).fetch()
        for univ in u:
            if univ.u_name.lower().replace(' ', '') == lower:
                self.response.headers['Content-Type'] = 'application/json'
                response = {
                    'status':'University already exist.',
                }
                self.response.out.write(json.dumps(response))
                return
        univ = University()
        univ.u_name = name
        univ.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))


class CreateCollege(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('colForm.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');    
    def post(self):
        name = self.request.get('college_name')
        lower = name.lower().replace(' ', '')
        c = College.query().order(+College.c_name).fetch()
        for col in c:
            if col.c_name.lower().replace(' ', '') == lower:
                self.response.headers['Content-Type'] = 'application/json'
                response = {
                    'status':'College already exist.',
                }
                self.response.out.write(json.dumps(response))
                return
        college = College()
        college.c_name = name
        college.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))

class CreateDepartment(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('depForm.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');    
    def post(self):
        name = self.request.get('department_name')
        lower = name.lower().replace(' ', '')
        d = Department.query().order(+Department.d_name).fetch()
        for dept in d:
            if dept.d_name.lower().replace(' ', '') == lower:
                self.response.headers['Content-Type'] = 'application/json'
                response = {
                    'status':'Department already exist.',
                }
                self.response.out.write(json.dumps(response))
                return
        dpt = Department()
        dpt.d_name = name
        dpt.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))

class  DeleteThesis(webapp2.RequestHandler):
    def get(self,th_id):
        d = Thesis.get_by_id(int(th_id))
        for studs in d.thesis_student_keys:
            s = studs.get()
            s.key.delete()
        d.key.delete()
        self.response.write('Thesis has been deleted <br> <a href="/thesis/list">Back to list of Theses</a>')

class ListFaculty(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        f = Faculty.query().order(+Faculty.f_last_name).fetch()
        template_data = {
            'faculty':f,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:    
            template = JINJA_ENVIRONMENT.get_template('facList.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');
class ListStudent(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        s = Student.query().order(+Student.s_last_name).fetch()
        template_data = {
            'student':s,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('studList.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('../login'); 
class ListUniversity(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        u = University.query().order(+University.u_name).fetch()
        template_data = {
            'university':u,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('univList.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('../login');

class ListDepartment(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        d = Department.query().order(+Department.d_name).fetch()
        template_data = {
            'department':d,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('depList.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');

class ListCollege(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        c = College.query().order(+College.c_name).fetch()
        template_data = {
            'college':c,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('colList.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');

class  DeleteStudent(webapp2.RequestHandler):
    def get(self,s_id):
        key_to_delete = ndb.Key('Student',int(s_id))
        th = Thesis.query(projection=[Thesis.thesis_student_keys]).fetch()
        for t in th:
            if key_to_delete in t.thesis_student_keys:
                thesis = t.key.get()
                idx = thesis.thesis_student_keys.index(key_to_delete)
                del thesis.thesis_student_keys[idx]
                thesis.put()
        s = key_to_delete.get()
        s.key.delete()
        self.response.write('Student has been deleted <br> <a href="/student/list">Back to list of Students</a>')

class StudentPage(webapp2.RequestHandler):
    def get(self,s_id):
        s = Student.get_by_id(int(s_id))
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'student': s,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('studPage.html')
        self.response.write(template.render(template_data))
        
    def post(self,s_id):
        s = Student.get_by_id(int(s_id))
        s.s_first_name = self.request.get('s_first_name')
        s.s_middle_name = self.request.get('s_middle_name')
        s.s_last_name = self.request.get('s_last_name')
        s.s_email = self.request.get('s_email')
        s.s_phone_num = self.request.get('s_phone_num')
        s.s_student_num = self.request.get('s_student_num')
        s.s_birthdate = self.request.get('s_birthdate')
        s.s_year_graduated = self.request.get('s_year_graduated')
        s.put()
        self.redirect('/')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login',LoginPage),
    ('/register',RegisterPage),
    ('/api/handler', APIHandlerPage),
    ('/thesis/delete/(.*)', DeleteThesis),
    ('/faculty/list', ListFaculty),
    ('/student/list', ListStudent),
    ('/university/list', ListUniversity),
    ('/college/list', ListCollege),
    ('/department/list', ListDepartment),
    ('/faculty/create', CreateFaculty),
    ('/student/create', CreateStudent),
    ('/university/create', CreateUniversity),
    ('/college/create', CreateCollege),
    ('/department/create', CreateDepartment),
    ('/thesis/list', ThesisList),
    ('/thesis/create', ThesisCreate),
    ('/csvimport', ImportCSV),
    ('/student/delete/(.*)', DeleteStudent),
    ('/student/page/(.*)', StudentPage)
], debug=True)