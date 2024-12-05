from collections import OrderedDict
import requests
from fake_useragent import UserAgent
import time
import calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

print("""
  __  __               _            _                 _____                                                       
 |  \/  |   __ _    __| |   ___    | |__    _   _    |  ___|   ___   _ __   _   _   _   _  __   __ __   __   __ _ 
 | |\/| |  / _` |  / _` |  / _ \   | '_ \  | | | |   | |_     / _ \ | '__| | | | | | | | | \ \ / / \ \ / /  / _` |
 | |  | | | (_| | | (_| | |  __/   | |_) | | |_| |   |  _|   |  __/ | |    | |_| | | |_| |  \ V /   \ V /  | (_| |
 |_|  |_|  \__,_|  \__,_|  \___|   |_.__/   \__, |   |_|      \___| |_|     \__, |  \__,_|   \_/     \_/    \__,_|
                                            |___/                           |___/""")



def generic_headers():
    user_agent = UserAgent().random
    headers = {
        'User-Agent': f"{user_agent}",
        'Content-Type': 'application/json'
    }
    return headers



class TaskLinks:
    def __init__(self, links):
        self.links = links
    def __repr__(self):
        return f"TaskLinks({self.links})"
    def __call__(self) -> list[str]:
        return self.links
    def __str__(self):
        return "\n".join(self.links)
    
    def tests(self) -> list[str]:
        """Получить из ссылок, только ссылки на тесты"""
        return [link for link in self.links if "naurok.com.ua/test" in link or "miyklas" in link or "vseosvi" in link or "wordwall" in link or  "forms.gle" in link]
    def naurok(self) -> list[str]:
        """Получить из ссылок, только ссылки на тесты Naurok"""
        return [link for link in self.links if "naurok.com.ua/test" in link]
    def miyklass(self) -> list[str]:
        """Получить из ссылок, только ссылки на тесты MiyKlass"""
        return [link for link in self.links if "miyklas" in link]
    def vseosvita(self) -> list[str]:
        """Получить из ссылок, только ссылки на тесты VseOsvita"""
        return [link for link in self.links if "vseosvita" in link]




class Human:
    def __init__(self, email: str, password: str) -> None:
        payload = {
            'email': email,
            'password': password
        }
        params = {
            "expand": "user,userTariff.tariffPlan,page=1",
            "_limit": "30"
        }
        self.email = email
        
        self.headers = generic_headers()
        self.cookies = requests.post('https://api.human.ua/v1/auth', headers=self.headers, json=payload).cookies
        response = requests.get('https://api.human.ua/v1/user/institutions', 
                                    headers=self.headers,
                                    cookies=self.cookies,
                                    params=params).json()
        try:
            self.human_id = response["institutions"][0]['id']
        except KeyError:
            raise KeyError("Неверно указаны данные для входа!")
        self.name = response['institutions'][0]['first_name']
    
    def __str__(self):
        return f"My name: {self.name}\nMy email: {self.email}\nMy human_id: {self.human_id}\nMy requests headers: {self.headers}"

    def get_tasks(self) -> list:
        """Получить все заданные задания"""
        result = []
        params = {
            "expand": "type.name,group.subject,home_tasks_user.assessment",
            "filter": "received",
            "_limit": "987654321"
        }
        response = requests.get(f'https://api.human.ua/v1/{self.human_id}/home-task/home-task/students-tasks', 
                                headers=self.headers, 
                                cookies=self.cookies,
                                params=params )
        for i in response.json():
            result.append(i)
        return result
    
    def get_this_weeks_lessons(self) -> list:
        """Получить все уроки к текущей неделе"""
        result = []
        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        start_of_week_timestamp = int(time.mktime(start_of_week.timetuple()))
        end_of_week_timestamp = int(time.mktime(end_of_week.timetuple()))

        params = {
            "dateStart": start_of_week_timestamp,
            "dateFinish": end_of_week_timestamp,
            "expand": "group.subject,webConference,classroom",
        }
        response = requests.get(f'https://api.human.ua/v1/{self.human_id}/calendar', 
                                headers=self.headers, 
                                cookies=self.cookies,
                                params=params)
        for i in response.json()['lessonEvents']:
            result.append(i)
        return result
    
    def get_nearest_lesson(self) -> list[dict, str]:
        """Получить ближайший урок"""
        now = datetime.now()
        start_of_day = datetime(year=now.year, month=now.month, day=now.day).timestamp()
        dates = []
        lessons = []
        params = {
            "dateStart": start_of_day,
            "dateFinish": start_of_day+86400,
            "expand": "group.subject,webConference,classroom"
        }
        while True:
            response = requests.get(f'https://api.human.ua/v1/{self.human_id}/calendar', 
                                    headers=self.headers, 
                                    cookies=self.cookies,
                                    params=params)
            for i in response.json()['lessonEvents']:
                if i['date'] > round(time.time()):
                    dates.append(i['date'])
                    lessons.append(i)
            if dates:
                nearest_date = min(dates, key=lambda x: abs(x - round(time.time())))
                position = dates.index(nearest_date)
                try:
                    return [lessons[position], lessons[position]['webConference']['url']]
                except:
                    return [lessons[position], None]
            
            start_of_day += 86400
    
    def get_all_tasks_links(self) -> list[str]:
        """Получить все ссылки из всех заданных заданий"""
        urls = []
        result = []
        def get_links(url) -> None:
            try:
                for task in url['lesson_tasks']:
                    if 'content' in task and 'blocks' in task['content']:
                        for block in task['content']['blocks']:
                            if 'link' in block['data']:
                                link = block['data']['link'].get('url')
                                if link:
                                    result.append(link)
            except:
                try:
                    for task in url['home_tasks']:
                        if 'content' in task and 'blocks' in task['content']:
                            for block in task['content']['blocks']:
                                if 'link' in block['data']:
                                    link = block['data']['link'].get('url')
                                    if link:
                                        result.append(link)
                except:
                    pass
        
        def get_task(url) -> None:
            params = {
                "expand": "members,home_tasks.assessments,home_tasks.recipients,home_tasks.type,home_tasks.home_tasks_users,home_tasks.files,home_tasks.links.attachment,home_tasks.content,lesson_tasks.type,lesson_tasks.assessments,lesson_tasks.content",
                "_limit": "987654321"
            
            }
            urls.append(requests.get(f"https://api.human.ua/v1/{self.human_id}/plan/theme/{url['theme']['id']}",
                                    headers=self.headers,
                                    cookies=self.cookies,
                                    params=params).json())

        with ThreadPoolExecutor(8) as get_task_executor:
            get_task_executor.map(get_task, self.get_tasks())
        
        

        with ThreadPoolExecutor(2) as check_executor:
            check_executor.map(get_links, urls)

        def tests():
            return [link for link in result if "naurok.com.ua/test" in link or "miyklas" in link or "vseosvi" in link or "wordwall" in link or "livework" in link]

        result.tests = tests

        return result
    
    def get_last_two_weeks_tasks_links(self) -> TaskLinks:
        """Получить все ссылки из всех заданных заданий, которые задали 2 недели назад и до текущего дня"""
        urls = []
        result = []
        def get_links(url) -> None:
            try:
                for task in url['lesson_tasks']:
                    if 'content' in task and 'blocks' in task['content']:
                        for block in task['content']['blocks']:
                            if 'link' in block['data']:
                                link = block['data']['link'].get('url')
                                if link:
                                    result.append(link)
            except:
                try:
                    for task in url['home_tasks']:
                        if 'content' in task and 'blocks' in task['content']:
                            for block in task['content']['blocks']:
                                if 'link' in block['data']:
                                    link = block['data']['link'].get('url')
                                    if link:
                                        result.append(link)
                except:
                    pass
        
        def get_task(url) -> None:
            if time.time() - 1209600 < int(url['published_at']):
                params = {
                    "expand": "members,home_tasks.assessments,home_tasks.recipients,home_tasks.type,home_tasks.home_tasks_users,home_tasks.files,home_tasks.links.attachment,home_tasks.content,lesson_tasks.type,lesson_tasks.assessments,lesson_tasks.content",
                    "_limit": "987654321"
                
                }
                urls.append(requests.get(f"https://api.human.ua/v1/{self.human_id}/plan/theme/{url['theme']['id']}",
                                        headers=self.headers,
                                        cookies=self.cookies,
                                        params=params).json())

        with ThreadPoolExecutor(8) as get_task_executor:
            get_task_executor.map(get_task, self.get_tasks())
        
        
        
        with ThreadPoolExecutor(2) as check_executor:
            check_executor.map(get_links, urls)

        return TaskLinks(result)
    
    def get_analytics(self) -> dict[str: list[int]]:
        """Получить 'Пiдсумковi' оценки\n\n
        \nВозвращает словарь
        'Название урока': [оценка1, оценка2]"""
        result = {}
        response = requests.get(f"https://api.human.ua/v1/{self.human_id}/analytics/common/student/1023544",
                                cookies=self.cookies,
                                headers=self.headers).json()
        
        for subject in response['thematicsAssessments']:
            print(subject['theme_container_title'])
            result[subject['subject_name']] = []

        for subject in response['thematicsAssessments']:
            result[subject['subject_name']].append(int(subject['int_value']))
        return result
    
    def get_tasks_tests_sort_by_subject(self, subject: str) -> TaskLinks:
        """Получить все тесты, сортировка по предмету"""
        result = []
        urls = []
        def get_links(url) -> None:
            try:
                for task in url['lesson_tasks']:
                    if 'content' in task and 'blocks' in task['content']:
                        for block in task['content']['blocks']:
                            if 'link' in block['data']:
                                link = block['data']['link'].get('url')
                                if link:
                                    result.append(link)
            except:
                try:
                    for task in url['home_tasks']:
                        if 'content' in task and 'blocks' in task['content']:
                            for block in task['content']['blocks']:
                                if 'link' in block['data']:
                                    link = block['data']['link'].get('url')
                                    if link:
                                        result.append(link)
                except:
                    pass
        def get_task(url) -> None:
            if subject in url['group']['subject']['i18n']['name']:
                params = {
                    "expand": "members,home_tasks.assessments,home_tasks.recipients,home_tasks.type,home_tasks.home_tasks_users,home_tasks.files,home_tasks.links.attachment,home_tasks.content,lesson_tasks.type,lesson_tasks.assessments,lesson_tasks.content",
                    "_limit": '987654321' #987654321
                
                }
                urls.append(requests.get(f"https://api.human.ua/v1/{self.human_id}/plan/theme/{url['theme']['id']}",
                                        headers=self.headers,
                                        cookies=self.cookies,
                                        params=params).json())
        
        with ThreadPoolExecutor(8) as get_task_executor:
            get_task_executor.map(get_task, self.get_tasks())
        
        

        with ThreadPoolExecutor(2) as check_executor:
            check_executor.map(get_links, urls)

        return TaskLinks(result)
    
    def get_tasks_tests_sort_by_date(self, date = 0) -> TaskLinks:
        """Получить все тесты, сортировка по дате\n
        0 = Текущая неделя\n
        1 = Прошлая неделя\n
        2 = Этот месяц\n
        3 = Прошлый месяц\n"""
        result = []
        urls = []
        def get_links(url) -> None:
            
            try:
                for task in url['lesson_tasks']:
                    if 'content' in task and 'blocks' in task['content']:
                        for block in task['content']['blocks']:
                            if 'link' in block['data']:
                                link = block['data']['link'].get('url')
                                if link:
                                    result.append(link)
            except:
                try:
                    for task in url['home_tasks']:
                        if 'content' in task and 'blocks' in task['content']:
                            for block in task['content']['blocks']:
                                if 'link' in block['data']:
                                    link = block['data']['link'].get('url')
                                    if link:
                                        result.append(link)
                except:
                    pass
        def get_task(url) -> None:
            params = {
                "expand": "members,home_tasks.assessments,home_tasks.recipients,home_tasks.type,home_tasks.home_tasks_users,home_tasks.files,home_tasks.links.attachment,home_tasks.content,lesson_tasks.type,lesson_tasks.assessments,lesson_tasks.content",
                "_limit": "987654321"
            }
            if date == 0 :
                today = datetime.today()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                start_of_week_timestamp = int(time.mktime(start_of_week.timetuple()))
                end_of_week_timestamp = int(time.mktime(end_of_week.timetuple()))

                if start_of_week_timestamp <= url['published_at'] <= end_of_week_timestamp:
                    urls.append(requests.get(f"https://api.human.ua/v1/{self.human_id}/plan/theme/{url['theme']['id']}",
                                            headers=self.headers,
                                            cookies=self.cookies,
                                            params=params).json())
            elif date == 1:
                today = datetime.today()
                start_of_week = today - timedelta(days=today.weekday())
                start_of_week -= timedelta(7)
                end_of_week = start_of_week + timedelta(days=6)
                start_of_week_timestamp = int(time.mktime(start_of_week.timetuple()))
                end_of_week_timestamp = int(time.mktime(end_of_week.timetuple()))

                if start_of_week_timestamp <= url['published_at'] <= end_of_week_timestamp:
                    urls.append(requests.get(f"https://api.human.ua/v1/{self.human_id}/plan/theme/{url['theme']['id']}",
                                            headers=self.headers,
                                            cookies=self.cookies,
                                            params=params).json())
            elif date == 2:
                now = datetime.now()
                start_of_month = datetime(now.year, now.month, 1, 0, 0, 0)
                
                last_day = calendar.monthrange(now.year, now.month)[1]
                end_of_month = datetime(now.year, now.month, last_day, 23, 59, 59)
                
                start_of_month_ts = int(start_of_month.timestamp())
                end_of_month_ts = int(end_of_month.timestamp())

                if start_of_month_ts <= url['published_at'] <= end_of_month_ts:
                    urls.append(requests.get(f"https://api.human.ua/v1/{self.human_id}/plan/theme/{url['theme']['id']}",
                                            headers=self.headers,
                                            cookies=self.cookies,
                                            params=params).json())
            elif date == 3:
                now = datetime.now()
                if now.month == 1:
                    year = now.year - 1
                    month = 12
                else:
                    year = now.year
                    month = now.month - 1
                start_of_last_month = datetime(year, month, 1, 0, 0, 0)
                
                last_day = calendar.monthrange(year, month)[1]
                end_of_last_month = datetime(year, month, last_day, 23, 59, 59)
                start_of_last_month_ts = int(start_of_last_month.timestamp())
                end_of_last_month_ts = int(end_of_last_month.timestamp())


                if start_of_last_month_ts <= url['published_at'] <= end_of_last_month_ts:
                    urls.append(requests.get(f"https://api.human.ua/v1/{self.human_id}/plan/theme/{url['theme']['id']}",
                                            headers=self.headers,
                                            cookies=self.cookies,
                                            params=params).json())
        
        with ThreadPoolExecutor(8) as get_task_executor:
            get_task_executor.map(get_task, self.get_tasks())
        
        
        with ThreadPoolExecutor(2) as check_executor:
            check_executor.map(get_links, urls)

        return TaskLinks(result)
    
    def get_my_courses(self) -> dict:
        """Получить все мои курсы"""
        params = {
            'expand': 'members,lesson_plans_count',
            '_limit': '987654321'
        }
        response = requests.get(f'https://api.human.ua/v1/{self.human_id}/group/courses/my-courses',
                                cookies = self.cookies,
                                headers = self.headers,
                                params=params)
        return response.json()
    
    def get_my_classmates(self) -> dict:
        """Получить human_id всех однаклассников\n
        В формате:\n
        {\n
            human_id: "Фио"\n
        }"""
        members = requests.get(f'https://api.human.ua/v1/{self.human_id}/group/group?expand=members.member',
                               cookies=self.cookies,
                               headers=self.headers).json()
        classmates = {}

        for member in members[0]['members']:
            if member['group_role_id'] > 4:
                classmates[member['user_id']] = (f"{member['member']['first_name']} {member['member']['last_name']} {member['member']['patronymic']}")
                
        return classmates
    
    def get_analytics_by_human_id(self, human_id: str | int) -> dict[str: list[int]]:
        result = {}
        response = requests.get(f"https://api.human.ua/v1/{self.human_id}/analytics/common/student/{human_id}",
                                cookies=self.cookies,
                                headers=self.headers).json()
        
        for subject in response['thematicsAssessments']:
            result[subject['subject_name']] = []

        for subject in response['thematicsAssessments']:
            try:
                result[subject['subject_name']].append(int(subject['int_value']))
            except:
                result[subject['subject_name']].append(None)
        return result
    
    def get_analytics_my_classmates_humanid_marks(self) -> dict[int: list]:
        result = {}
        classmates = self.get_my_classmates()
        def get_human_id_marks(id):
            try:
                marks = []
                response = self.get_analytics_by_human_id(id)
                if response:
                    for a in response:
                        for mark in response[a]:
                            if mark:
                                marks.append(mark) 
                if marks:
                    id = id, classmates[id]
                    if id == self.human_id:
                        id = 'You'
                    result[id] = marks
            except Exception as ex:
                print(ex)
                pass

        
        with ThreadPoolExecutor(len(classmates)/2) as executor:
            executor.map(get_human_id_marks, classmates)
        
        return result
    
    def get_leaderboard_my_classmates(self) -> dict:
        """Таблица лидеров одноклассников\n
        Возвращает словарь: \n
        {\n
            human_id: место_в_топе\n
        }"""
        analytics = self.get_analytics_my_classmates_humanid_marks()
        new_dict = {}
        for human_id, marks in analytics.items():
            if marks:
                new_dict[human_id] = round(sum(marks) / len(marks), 2)

        sorted_analytics = OrderedDict(
            sorted(new_dict.items(), key=lambda item: item[1], reverse=True)
        )

        result = {human_id[1]: rank for rank, human_id in enumerate(sorted_analytics, start=1)}

        result = OrderedDict(sorted(result.items(), key=lambda item: item[1]))

        return result

    def get_group_id(self):
        response = requests.get(f'https://api.human.ua/v1/{self.human_id}/group/group', 
                            headers=self.headers,
                            cookies=self.cookies)
        return response.json()[0]['id']



    def test(self):
        params = {
            "expand": "members.member",
            # "type_id": "1"
        }
        response = requests.get(f"https://api.human.ua/v1/{self.human_id}/group/group/{self.get_group_id()}",
                                cookies=self.cookies,
                                headers=self.headers,
                                params=params)
        return response

