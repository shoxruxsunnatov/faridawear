from datetime import datetime, timedelta

from django.views.generic import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from main.models import Group, Topic
from exams.models import Exam
from dictionary.models import (
    VocabularyPackage,
    DictionaryExam,
    DictionaryExamSession
)
from account.models import (
    User,
    UserGroupLink
)

from main.variables import INT_TO_LEVEL
from main.gpt import generate
from account.security import AdminRoleRequired
from account.utils import (
    get_clean_text,
    generate_username,
    generate_password
)
from payment.utils import charge_group_tuition


class GroupsListViewAPI(AdminRoleRequired, View):

    def post(self, req):
        title = req.POST.get('title', '').strip()

        data = {
            'message': 'failed'
        }

        if len(title) > 0:
            group = Group.objects.create(title=title, organization=req.user.organization)
            link = UserGroupLink.objects.create(user=req.user, group=group)

            data['message'] = 'success'
        
        return JsonResponse(data, safe=False)
    
    def get(self, req):

        if req.user.role == 'supervisor':
            data = [
                {
                    'id': group.id,
                    'title': group.title
                }
                for group in Group.objects.filter(organization=req.user.organization)
            ]
        
        else:
            data = [
                {
                    'id': link.group.id,
                    'title': link.group.title
                }
                for link in req.user.group_links.all()
            ]

        return JsonResponse(data, safe=False)


class GroupDetailViewAPI(AdminRoleRequired, View):

    def post(self, req, pk):
        
        group = get_object_or_404(Group, id=pk)

        if req.user.role == 'teacher':
            link = get_object_or_404(UserGroupLink, group=group, user=req.user)

        first_name = req.POST.get('first_name', '').strip()
        last_name = req.POST.get('last_name', '').strip()
        phone1 = req.POST.get('phone1', '').strip()
        phone2 = req.POST.get('phone2', '').strip()
        details = req.POST.get('details', '').strip()

        full_name = get_clean_text(first_name + last_name)

        data = {
            'message': 'failed'
        }

        if len(full_name) >= 5:
            student = User(
                first_name=first_name,
                last_name=last_name,
                phone1=phone1,
                phone2=phone2,
                details=details,
                role='student',
                organization=group.organization,
                group=group,
                username=generate_username(User, full_name),
            )
            student.save()
            data['message'] = 'success'
        
        else:
            data['error'] = 'invalid-name'
        
        return JsonResponse(data, safe=False)
    
    def get(self, req, pk):

        group = get_object_or_404(Group, id=pk)
        charge_group_tuition(group)

        if req.user.role == 'teacher':
            link = get_object_or_404(UserGroupLink, group=group, user=req.user)

        data = {
            'group': {
                'title': group.title
            },
            'students': [            
                {
                    'id': student.id,
                    'full_name': student.get_full_name(),
                    'grammar_level': student.get_grammar_level_display(),
                    'vocabulary_level': student.get_vocabulary_level_display(),
                    'rating': student.rating,
                    'date_joined': student.date_joined,
                    'is_paid': student.is_paid
                }
                for student in group.students.order_by('-rating', 'first_name', 'last_name')
            ]
        }

        return JsonResponse(data, safe=False)


class TopicsListViewAPI(AdminRoleRequired, View):

    def post(self, req):
        title = req.POST.get('title', '').strip()
        index = req.POST.get('index', '').strip()
        prompt = req.POST.get('prompt', '').strip()

        data = {
            'message': 'failed',
        }
        errors = []

        try:
            index = int(index)
        except ValueError:
            errors.append('index')
        
        if not 4 < len(title) < 200:
            errors.append('title')
        
        if not len(title) < len(prompt) < 200:
            errors.append('prompt')
        
        if not req.user.role == 'supervisor':
            errors.append('permission')
            
        if not errors:
            topic = Topic(title=title, index=index, prompt=prompt)
            topic.save()

            data['message'] = 'success'
        
        else:
            data['errors'] = errors

        return JsonResponse(data, safe=False)
    
    def get(self, req):

        data = [
            {
                'id': topic.id,
                'index': topic.index,
                'title': topic.title,
                'prompt': topic.prompt
            }
            for topic in Topic.objects.order_by('index', 'id')
        ]

        return JsonResponse(data, safe=False)

    
class TopicDetailViewAPI(AdminRoleRequired, View):

    def post(self, req, pk):

        topic = get_object_or_404(Topic, id=pk)
        title = req.POST.get('title', '').strip()
        index = req.POST.get('index', '').strip()
        prompt = req.POST.get('prompt', '').strip()

        data = {
            'message': 'failed',
        }
        errors = []

        try:
            index = int(index)
        except ValueError:
            errors.append('index')
        
        if not 4 < len(title) < 200:
            errors.append('title')
        
        if not len(title) < len(prompt) < 200:
            errors.append('prompt')
        
        if not req.user.role == 'supervisor':
            errors.append('permission')
        
        if not errors:
            topic.title = title
            topic.index = index
            topic.prompt = prompt
            topic.save()

            data['message'] = 'success'
        
        else:
            data['errors'] = errors

        return JsonResponse(data, safe=False)


    def get(self, req, pk):

        topic = get_object_or_404(Topic, id=pk)

        data = {
            'id': topic.id,
            'title': topic.title,
            'prompt': topic.prompt
        }

        return JsonResponse(data, safe=False)


class TestsListViewAPI(AdminRoleRequired, View):

    def post(self, req, pk):

        topic = get_object_or_404(Topic, id=pk)
        level = req.POST.get('level', '').strip()

        data = {
            'message': 'failed',
            'tests': []
        }
        errors = []
        
        if level not in INT_TO_LEVEL:
            errors.append('level')
        
        if not errors:
            try:
                tests = generate(topic=topic, level=level, model="gpt-4o-mini")
            except:
                errors.append('gpt')
            
            else:
            
                for test in tests:
                    options = [
                        {
                            "id": option.id,
                            "text": option.text
                        }
                        for option in test.options.all()
                    ]
                    
                    data['tests'].append({
                        "id": test.id,
                        "text": test.text,
                        "answer": test.answer.text,
                        "options": options,
                        "level": test.get_level_display()
                    })
                

                data['message'] = 'success'
        
        else:
            data['errors'] = errors

        return JsonResponse(data, safe=False)


class ExamsListViewAPI(AdminRoleRequired, View):

    def post(self, req, *args, **kwargs):

        title = req.POST.get('title', '').strip()
        start_hour = req.POST.get('start_hour', '').strip()
        start_minute = req.POST.get('start_minute', '').strip()
        duration = req.POST.get('duration', '').strip()
        max_sessions = req.POST.get('max_sessions', '').strip()
        topic = req.POST.get('topic', '').strip()

        is_preset = None
        errors = []

        if len(title) < 3:
            errors.append('title')
        
        try:
            start_hour = int(start_hour)
            if not 0 <= start_hour < 24:
                raise ValueError("start_hour")
        except ValueError:
            errors.append('start_hour')
        
        try:
            start_minute = int(start_minute)
            if not 0 <= start_minute < 60:
                raise ValueError("start_minute")
        except ValueError:
            errors.append('start_minute')

        try:
            duration = int(duration)
        except ValueError:
            errors.append('duration')
        else:
            if not 9 < duration < 121:
                errors.append('duration')
        
        now = timezone.make_aware(datetime.now())
        start_date = timezone.make_aware(datetime(now.year, now.month, now.day, start_hour, start_minute))
        end_date = start_date + timedelta(minutes=duration)

        if now > start_date:
            errors.append('start_date')

        try:
            max_sessions = int(max_sessions)
        except ValueError:
            errors.append('max_sessions')
        else:
            if not 0 < max_sessions < 1000:
                errors.append('max_sessions')
        
        if topic == "optional":
            is_preset = False
        
        else:
            try:
                topic = int(topic)
                is_preset = True
            except ValueError:
                errors.append('topic')
            else:
                topic = Topic.objects.filter(id=topic).first()
                if not topic:
                    errors.append('topic')
        
        data = {"message": "failed"}

        if not errors:

            exam = Exam(
                title=title,
                author=req.user,
                max_sessions=max_sessions,
                is_preset=is_preset,
                is_recorded=True,
                use_gpt=True,
                is_training=False,
                start_date=start_date,
                end_date=end_date
            )
            if is_preset:
                exam.topic = topic
            
            exam.save()
            data["message"] = "success"

        else:
            data["errors"] = errors
        
        
        return JsonResponse(data, safe=False)


class VocabularyPackageDetailViewAPI(AdminRoleRequired, View):
    
    def post(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="supervisor")

        data = {
            "message": "failed",
            "errors": []
        }
        title = req.POST.get("title", "").strip()

        if not (req.user.has_perm("account.edit_dictionary") or req.user.role == "supervisor"):
            data["errors"].append("permission")
        
        if not 2 < len(title) < 101:
            data["errors"].append("length")
        
        if not data["errors"]:
            vp.title = title
            vp.save()

            data["message"] = "success"
        
        return JsonResponse(data, safe=False)


    def delete(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk)

        data = {
            "message": "failed",
            "errors": []
        }

        if not (req.user.has_perm("account.edit_dictionary") or req.user.role == "supervisor"):
            data["errors"].append("permission")
        
        if not data["errors"]:
            vp.delete()
            data["message"] = "success"
        
        return JsonResponse(data, safe=False)


class DictionaryExamsListViewAPI(AdminRoleRequired, View):

    def post(self, req, *args, **kwargs):

        title = req.POST.get('title', '').strip()
        start_hour = req.POST.get('start_hour', '').strip()
        start_minute = req.POST.get('start_minute', '').strip()
        duration = req.POST.get('duration', '').strip()
        max_sessions = req.POST.get('max_sessions', '').strip()
        package = req.POST.get('package', '').strip()

        is_preset = None
        errors = []

        if len(title) < 3:
            errors.append('title')
        
        try:
            start_hour = int(start_hour)
            if not 0 <= start_hour < 24:
                raise ValueError("start_hour")
        except ValueError:
            errors.append('start_hour')
        
        try:
            start_minute = int(start_minute)
            if not 0 <= start_minute < 60:
                raise ValueError("start_minute")
        except ValueError:
            errors.append('start_minute')

        try:
            duration = int(duration)
        except ValueError:
            errors.append('duration')
        else:
            if not 9 < duration < 121:
                errors.append('duration')
        
        now = timezone.make_aware(datetime.now())
        start_date = timezone.make_aware(datetime(now.year, now.month, now.day, start_hour, start_minute))
        end_date = start_date + timedelta(minutes=duration)

        if now > start_date:
            errors.append('start_date')

        try:
            max_sessions = int(max_sessions)
        except ValueError:
            errors.append('max_sessions')
        else:
            if not 0 < max_sessions < 1000:
                errors.append('max_sessions')
        
        if package == "optional_supervisor" or package == "optional_student":
            is_preset = False
        
        else:
            try:
                package = int(package)
                is_preset = True
            except ValueError:
                errors.append('package')
            else:
                package = VocabularyPackage.objects.filter(id=package).first()
                if not package or package.vocabularies.count() < 100:
                    errors.append('package')
        
        data = {"message": "failed"}

        if not errors:

            exam = DictionaryExam(
                title=title,
                author=req.user,
                max_sessions=max_sessions,
                is_preset=is_preset,
                is_recorded=True,
                is_training=False,
                created_by="supervisor",
                package_source=package.replace("optional_", ""),
                start_date=start_date,
                end_date=end_date,
                organization=req.user.organization
            )
            if is_preset:
                exam.package = package
            
            exam.save()
            data["message"] = "success"

        else:
            data["errors"] = errors
        
        
        return JsonResponse(data, safe=False)


class LockStatusAPI(AdminRoleRequired, View):

    def post(self, req, *args, **kwargs):
        
        data = {
            "message": "failed",
            "errors": []
        }

        exam_session_id = req.POST.get('exam_session_id', '0').strip()
        is_locked = req.POST.get('is_locked', '').strip()

        exam_session = DictionaryExamSession.objects.filter(id=exam_session_id).first()
        if not exam_session:
            data["errors"].append("invalid-id")
        else:
            if exam_session.is_finished or exam_session.is_training:
                data["errors"].append("expired")

        if is_locked not in ('0', '1'):
            data["errors"].append("is_locked")


        if not data["errors"]:
            exam_session.is_locked = bool(int(is_locked))
            exam_session.is_lock_reset = True
            exam_session.save()

            data.update(
                {
                    "message": "success",
                }
            )
            
        return JsonResponse(data, safe=False)


class StudentDetailViewAPI(AdminRoleRequired, View):

    def post(self, req, pk):
        
        student = get_object_or_404(User, id=pk, role="student")

        first_name = req.POST.get('first_name', '').strip()
        last_name = req.POST.get('last_name', '').strip()
        phone1 = req.POST.get('phone1', '').strip()
        phone2 = req.POST.get('phone2', '').strip()
        details = req.POST.get('details', '').strip()

        data = {
            'message': 'failed',
            'errors': []
        }

        if not 2 < len(first_name) < 50:
            data['errors'].append('first_name')
        
        if not 2 < len(last_name) < 50:
            data['errors'].append('last_name')
        
        if not 0 <= len(phone1) < 50:
            data['errors'].append('phone1')
        
        if not 0 <= len(phone2) < 50:
            data['errors'].append('phone2')
        
        if not 0 <= len(details) < 300:
            data['errors'].append('details')

        if not data['errors']:
            student.first_name = first_name
            student.last_name = last_name
            student.phone1 = phone1
            student.phone2 = phone2
            student.details = details
            student.save()

            data['message'] = 'success'
                
        return JsonResponse(data, safe=False)

