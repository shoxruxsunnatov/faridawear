import re
import spacy
from datetime import datetime, timedelta

from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone

from account.security import (
    CSRFExempt,
    AdminRoleRequired
)
from dictionary.models import (
    VocabularyPackage,
    Vocabulary,
    DictionaryExam,
    VocabularyTest,
    VocabularyTestOption,
    DictionaryExamSession
)

from admins.api import (
    VocabularyPackageDetailViewAPI as TeacherVocabularyPackageDetailViewAPI,
    DictionaryExamsListViewAPI as TeacherDictionaryExamsListViewAPI,
    LockStatusAPI as TeacherLockStatusAPI
)
from students.api import (
    DictionaryExamDetailViewAPI as StudentDictionaryExamDetailViewAPI,
    LockStatusAPI as StudentLockStatusAPI
)
from dictionary.utils import (
    check_text,
    vocabulary_chart,
    check_participation,
    get_ongoing_session,
    delete_expired_exams,
    delete_expired_sessions,
    delete_expired_session,
    end_exam_session
)
from dictionary.gpt import (
    generate_examples,
    generate_passage
)
from reading.gpt import (
    get_full_vocabulary
)

nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])


class VocabularyPackagesViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        
        data = {
            "message": "failed",
            "errors": []
        }

        title = req.POST.get('title', '').strip()

        if not (req.user.has_perm("account.edit_dictionary") or req.user.role == "supervisor"):
            data["errors"].append("permission")
        
        if not 2 < len(title) < 100:
            data["errors"].append('length')

        if not data["errors"]:
            vp = VocabularyPackage(
                title=title,
                author=req.user,
                created_by="supervisor",
                organization=req.user.organization
            )
            vp.save()

            data.update({
                "message": "success",
                "vocabulary_package": {
                    "id": vp.id,
                }
            })
        
        return JsonResponse(data, safe=False)

    def get(self, req, *args, **kwargs):

        package_source = req.GET.get("package_source", "supervisor")

        if package_source == "supervisor":
            packages = VocabularyPackage.objects.filter(created_by=package_source, organization=req.user.organization)
        elif package_source == "student":
            packages = VocabularyPackage.objects.filter(author=req.user, created_by=package_source)

        data = [
            {
                "id": vp.id,
                "title": vp.title,
                "count": vp.vocabularies.count(),
                "author": vp.author.get_full_name() if vp.author else None,
                "date_created": vp.date_created
            }
            for vp in packages
        ]

        return JsonResponse(data, safe=False)


class VocabularyPackageDetailViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, pk, *args, **kwargs):

        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherVocabularyPackageDetailViewAPI.as_view()
        else:
            view = HttpResponse
        
        return view(req, pk, *args, **kwargs)

    def get(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="supervisor")

        data = {
            "id": vp.id,
            "title": vp.title,
            "count": vp.vocabularies.count(),
            "author": vp.author.get_full_name() if vp.author else None,
            "date_created": vp.date_created
        }

        return JsonResponse(data, safe=False)
    
    def delete(self, req, pk, *args, **kwargs):

        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherVocabularyPackageDetailViewAPI.as_view()
        else:
            view = HttpResponse
        
        return view(req, pk, *args, **kwargs)


class MyVocabularyPackagesViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        
        data = {
            "message": "failed",
            "errors": []
        }

        title = req.POST.get('title', '').strip()

        if not 2 < len(title) < 100:
            data["errors"].append('length')

        if not data["errors"]:
            vp = VocabularyPackage(
                title=title,
                author=req.user,
                created_by="student",
                organization=req.user.organization
            )
            vp.save()

            data.update({
                "message": "success",
                "vocabulary_package": {
                    "id": vp.id,
                }
            })
        
        return JsonResponse(data, safe=False)

    def get(self, req, *args, **kwargs):

        data = [
            {
                "id": vp.id,
                "title": vp.title,
                "count": vp.vocabularies.count(),
                "author": vp.author.get_full_name() if vp.author else None,
                "date_created": vp.date_created
            }
            for vp in VocabularyPackage.objects.filter(author=req.user, created_by="student").order_by("-id")
        ]

        return JsonResponse(data, safe=False)


class MyVocabularyPackageDetailViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def get(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="student")

        data = {
            "id": vp.id,
            "title": vp.title,
            "count": vp.vocabularies.count(),
            "author": vp.author.get_full_name() if vp.author else None,
            "date_created": vp.date_created
        }

        return JsonResponse(data, safe=False)
    
    def post(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="student")

        data = {
            "message": "failed",
            "errors": []
        }
        title = req.POST.get("title", "").strip()

        if vp.author != req.user:
            data["errors"].append("permission")
        
        if not 2 < len(title) < 101:
            data["errors"].append("length")
        
        if not data["errors"]:
            vp.title = title
            vp.save()

            data["message"] = "success"
        
        return JsonResponse(data, safe=False)


    def delete(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="student")

        data = {
            "message": "failed",
            "errors": []
        }

        if vp.author != req.user:
            data["errors"].append("permission")
        
        if not data["errors"]:
            vp.delete()
            data["message"] = "success"
        
        return JsonResponse(data, safe=False)


class PrintVocabularyPackageViewAPI(AdminRoleRequired, View):

    def get(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk)
        
        vocabularies = [
            {
                "id": vocabulary.id,
                "text": vocabulary.text,
                "translation": vocabulary.translation,
                "description": vocabulary.description,
            }
            for vocabulary in vp.vocabularies.all()
        ]

        data = {
            "title": vp.title,
            "vocabularies": vocabularies
        }

        return JsonResponse(data, safe=False)


class PrintMyVocabularyPackageViewAPI(View):

    def get(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, author=req.user)
        
        vocabularies = [
            {
                "id": vocabulary.id,
                "text": vocabulary.text,
                "translation": vocabulary.translation,
                "description": vocabulary.description,
            }
            for vocabulary in vp.vocabularies.all()
        ]

        data = {
            "title": vp.title,
            "vocabularies": vocabularies
        }

        return JsonResponse(data, safe=False)
    

class VocabularyAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="supervisor")
        data = {
            "message": "failed",
            "errors": [],
        }

        text = req.POST.get("text", "").strip().replace('’', "'")
        text =  re.sub(r'\s+', ' ', text)
        translation = req.POST.get("translation", "").strip()
        description = req.POST.get("description", "").strip()
        category = req.POST.get("category", "").strip()
        image = req.FILES.get('image')
        auto_generate = req.POST.get("auto_generate")
        

        if not 1 < len(text) < 200:
            data["errors"].append("text-translation")
        else:
            text = nlp(text)[0].lemma_.lower()
        
        if auto_generate != "on":
            if not 1 < len(translation) < 200:
                data["errors"].append("text-translation")

            if not len(description) < 300:
                data["errors"].append("description")
            
            if category not in ("other", "noun", "adjective", "verb"):
                data["errors"].append("category")

        if not (req.user.has_perm("account.edit_dictionary") or req.user.role == "supervisor"):
            data["errors"].append("permission")

        if vp.vocabularies.count() >= 50:
            data["errors"].append("capacity")
        
        existing = Vocabulary.objects.filter(text=text.lower(), created_by="supervisor", organization=req.user.organization).first()
        if existing:
            data["existing"] = {
                "id": existing.id,
                "text": existing.text,
                "translation": existing.translation,
                "description": existing.description,
                "package": existing.package.title,
                "author": existing.author.get_full_name() if existing.author else None,
                "date_created": existing.date_created
            }
            data["errors"].append("existing")

        if image:
            if image.name.split('.')[-1].lower() not in ['png', 'jpg', 'jfif']:
                data["errors"].append("image")
        # else:
        #     data["errors"].append("image")

        if not data["errors"]:

            spelling_check = check_text(text)
            if not spelling_check:
                
                if auto_generate == "on":
                    sys_vocabulary = Vocabulary.objects.filter(text=text, created_by="system").first()
                    if sys_vocabulary:
                        vocabulary = Vocabulary(
                            author=req.user,
                            parent=sys_vocabulary,
                            package=vp,
                            text=sys_vocabulary.text,
                            translation=sys_vocabulary.translation,
                            description=sys_vocabulary.description,
                            category=sys_vocabulary.category,
                            created_by="supervisor",
                            organization=req.user.organization
                        )
                    else:

                        response = get_full_vocabulary(text)
                        if not response:
                            return JsonResponse(data, safe=False)
                        
                        sys_vocabulary = Vocabulary(
                            text=text,
                            translation=response[0].strip(),
                            description=response[2].strip(),
                            category=response[1].strip(),
                            created_by="system",
                            organization=req.user.organization
                        )
                        sys_vocabulary.save()

                        vocabulary = Vocabulary(
                            author=req.user,
                            parent=sys_vocabulary,
                            package=vp,
                            text=text,
                            translation=response[0].strip(),
                            description=response[2].strip(),
                            category=response[1].strip(),
                            created_by="supervisor",
                            organization=req.user.organization
                        )
                else:
                    vocabulary = Vocabulary(
                        author=req.user,
                        package=vp,
                        text=text,
                        translation=translation,
                        description=description,
                        category=category,
                        created_by="supervisor",
                        organization=req.user.organization
                    )
                    
                if image:
                    vocabulary.image = image
                vocabulary.save()

                data["message"] = "success"
            
            else:
                data.update(
                    {
                        "errors": ["spelling"],
                        "suggestions": spelling_check
                    }
                )
        
        return JsonResponse(data, safe=False)


    def get(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk)
        
        data = [
            {
                "id": vocabulary.id,
                "text": vocabulary.text,
                "translation": vocabulary.translation,
                "description": vocabulary.description,
                "author": vocabulary.author.get_full_name() if vocabulary.author else None,
                "image": vocabulary.image.url if vocabulary.image else None,
                "category": vocabulary.category,
                "date_created": vocabulary.date_created
            }
            for vocabulary in vp.vocabularies.all()
        ]

        return JsonResponse(data, safe=False)


class MyVocabularyAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="student")
        data = {
            "message": "failed",
            "errors": [],
        }

        text = req.POST.get("text", "").strip().replace('’', "'")
        text =  re.sub(r"[^a-zA-z'-]", '', text)

        if not 1 < len(text) < 200:
            data["errors"].append("text-translation")
        else:
            text = nlp(text)[0].lemma_.lower()

        if vp.author != req.user:
            data["errors"].append("permission")

        if vp.vocabularies.count() >= 50:
            data["errors"].append("capacity")
        
        existing = Vocabulary.objects.filter(text=text, author=req.user, created_by="student").first()
        if existing:
            data["existing"] = {
                "id": existing.id,
                "text": existing.text,
                "translation": existing.translation,
                "description": existing.description,
                "package": existing.package.title,
                "author": existing.author.get_full_name() if existing.author else None,
                "date_created": existing.date_created
            }
            data["errors"].append("existing")

        if not data["errors"]:

            spelling_check = check_text(text)
            if not spelling_check:

                sys_vocabulary = Vocabulary.objects.filter(text=text, created_by="system").first()
                if sys_vocabulary:
                    vocabulary = Vocabulary(
                        author=req.user,
                        parent=sys_vocabulary,
                        package=vp,
                        text=sys_vocabulary.text,
                        translation=sys_vocabulary.translation,
                        description=sys_vocabulary.description,
                        category=sys_vocabulary.category,
                        created_by="student",
                        organization=req.user.organization
                    )
                    vocabulary.save()
                
                else:

                    response = get_full_vocabulary(text)
                    if not response:
                        return JsonResponse(data, safe=False)
                    
                    sys_vocabulary = Vocabulary(
                        text=text,
                        translation=response[0].strip(),
                        description=response[2].strip(),
                        category=response[1].strip(),
                        created_by="system",
                        organization=req.user.organization
                    )
                    sys_vocabulary.save()

                    vocabulary = Vocabulary(
                        author=req.user,
                        parent=sys_vocabulary,
                        package=vp,
                        text=text,
                        translation=response[0].strip(),
                        description=response[2].strip(),
                        category=response[1].strip(),
                        created_by="student",
                        organization=req.user.organization
                    )
                    vocabulary.save()
            
                data["message"] = "success"
            
            else:
                data.update(
                    {
                        "errors": ["spelling"],
                        "suggestions": spelling_check
                    }
                )
        
        return JsonResponse(data, safe=False)
    

    # old function
    # def post(self, req, pk, *args, **kwargs):

    #     vp = get_object_or_404(VocabularyPackage, id=pk, created_by="student")
    #     data = {
    #         "message": "failed",
    #         "errors": [],
    #     }

    #     text = req.POST.get("text", "").strip().replace('’', "'")
    #     text =  re.sub(r'\s+', ' ', text)
    #     translation = req.POST.get("translation", "").strip()
    #     description = req.POST.get("description", "").strip()
    #     category = req.POST.get("category", "").strip()
    #     image = req.FILES.get('image')

    #     if not 1 < len(text) < 200 or not 1 < len(translation) < 200:
    #         data["errors"].append("text-translation")
    #     else:
    #         text = nlp(text)[0].lemma_

    #     if not len(description) < 300:
    #         data["errors"].append("description")

    #     if vp.author != req.user:
    #         data["errors"].append("permission")

    #     if vp.vocabularies.count() >= 50:
    #         data["errors"].append("capacity")
        
    #     existing = Vocabulary.objects.filter(text=text.lower(), author=req.user, created_by="student").first()
    #     if existing:
    #         data["existing"] = {
    #             "id": existing.id,
    #             "text": existing.text,
    #             "translation": existing.translation,
    #             "description": existing.description,
    #             "package": existing.package.title,
    #             "author": existing.author.get_full_name() if existing.author else None,
    #             "date_created": existing.date_created
    #         }
    #         data["errors"].append("existing")

    #     if image:
    #         if image.name.split('.')[-1].lower() not in ['png', 'jpg', 'jfif']:
    #             data["errors"].append("image")
        
    #     if category not in ("other", "noun", "adjective", "verb"):
    #         data["errors"].append("category")


    #     if not data["errors"]:

    #         spelling_check = check_text(text)
    #         if not spelling_check:
    #             vocabulary = Vocabulary(
    #                 author=req.user,
    #                 package=vp,
    #                 text=text.lower(),
    #                 translation=translation,
    #                 description=description,
    #                 image=image,
    #                 category=category,
    #                 created_by="student"
    #             )
    #             vocabulary.save()

    #             data["message"] = "success"
            
    #         else:
    #             data.update(
    #                 {
    #                     "errors": ["spelling"],
    #                     "suggestions": spelling_check
    #                 }
    #             )
        
    #     return JsonResponse(data, safe=False)


    def get(self, req, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=pk, created_by="student")
        
        data = [
            {
                "id": vocabulary.id,
                "text": vocabulary.text,
                "translation": vocabulary.translation,
                "description": vocabulary.description,
                "author": vocabulary.author.get_full_name() if vocabulary.author else None,
                "image": vocabulary.image.url if vocabulary.image else None,
                "category": vocabulary.category,
                "date_created": vocabulary.date_created
            }
            for vocabulary in vp.vocabularies.order_by("-date_created").all()
        ]

        return JsonResponse(data, safe=False)
    

class VocabularyDetailAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, package_id, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=package_id)
        vocabulary = get_object_or_404(Vocabulary, id=pk)
        data = {
            "message": "failed",
            "errors": [],
        }

        text = req.POST.get("text", "").strip()
        text =  re.sub(r'\s+', ' ', text)
        translation = req.POST.get("translation", "").strip()
        description = req.POST.get("description", "").strip()

        if not 1 < len(text) < 200 or not 1 < len(translation) < 200:
            data["errors"].append("text-translation")

        if not len(description) < 300:
            data["errors"].append("description")

        if not (req.user.has_perm("account.edit_dictionary") or req.user.role == "supervisor"):
            data["errors"].append("permission")
        
        existing = Vocabulary.objects.filter(text=text.lower(), created_by="supervisor", organization=req.user.organization).first()
        if existing and existing != vocabulary:
            data["existing"] = {
                "id": existing.id,
                "text": existing.text,
                "translation": existing.translation,
                "description": existing.description,
                "package": existing.package.title,
                "author": existing.author.get_full_name() if existing.author else None,
                "date_created": existing.date_created
            }
            data["errors"].append("existing")

        if not data["errors"]:

            spelling_check = check_text(text)
            if not spelling_check:
                vocabulary.text = text.lower()
                vocabulary.translation = translation
                vocabulary.description = description
                vocabulary.save()

                data["message"] = "success"
            
            else:
                data.update(
                    {
                        "errors": ["spelling"],
                        "suggestions": spelling_check
                    }
                )
        
        return JsonResponse(data, safe=False)
    
    def delete(self, req, package_id, pk, *args, **kwargs):

        vocabulary = get_object_or_404(Vocabulary, id=pk)

        data = {
            "message": "failed",
            "errors": []
        }

        if not (req.user.has_perm("account.edit_dictionary") or req.user.role == "supervisor"):
            data["errors"].append("permission")
        
        if not data["errors"]:
            vocabulary.delete()
            data["message"] = "success"
        
        return JsonResponse(data, safe=False)


class MyVocabularyDetailAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, package_id, pk, *args, **kwargs):

        vp = get_object_or_404(VocabularyPackage, id=package_id, created_by="student")
        vocabulary = get_object_or_404(Vocabulary, id=pk, created_by="student")
        data = {
            "message": "failed",
            "errors": [],
        }

        text = req.POST.get("text", "").strip()
        text =  re.sub(r'\s+', ' ', text)
        translation = req.POST.get("translation", "").strip()
        description = req.POST.get("description", "").strip()

        if not 1 < len(text) < 200 or not 1 < len(translation) < 200:
            data["errors"].append("text-translation")

        if not len(description) < 300:
            data["errors"].append("description")

        if vocabulary.author != req.user:
            data["errors"].append("permission")
        
        existing = Vocabulary.objects.filter(text=text.lower(), author=req.user, created_by="student").first()
        if existing and existing != vocabulary:
            data["existing"] = {
                "id": existing.id,
                "text": existing.text,
                "translation": existing.translation,
                "description": existing.description,
                "package": existing.package.title,
                "author": existing.author.get_full_name() if existing.author else None,
                "date_created": existing.date_created
            }
            data["errors"].append("existing")

        if not data["errors"]:

            spelling_check = check_text(text)
            if not spelling_check:
                vocabulary.text = text.lower()
                vocabulary.translation = translation
                vocabulary.description = description
                vocabulary.save()

                data["message"] = "success"
            
            else:
                data.update(
                    {
                        "errors": ["spelling"],
                        "suggestions": spelling_check
                    }
                )
        
        return JsonResponse(data, safe=False)
    
    def delete(self, req, package_id, pk, *args, **kwargs):

        vocabulary = get_object_or_404(Vocabulary, id=pk, created_by="student")

        data = {
            "message": "failed",
            "errors": []
        }

        if vocabulary.author != req.user:
            data["errors"].append("permission")
        
        if not data["errors"]:
            vocabulary.delete()
            data["message"] = "success"
        
        return JsonResponse(data, safe=False)


class VocabularyDetailViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def get(self, req, package_id, pk, *args, **kwargs):

        package = get_object_or_404(VocabularyPackage, id=package_id)
        vocabulary = get_object_or_404(Vocabulary, id=pk)

        data = {
            "message": "succes",
            "errors": []
        }

        vm = vocabulary.metas.first()        
        if not vm:
            examples = generate_examples(vocabulary)
            while not examples:
                examples = generate_examples(vocabulary)
            
            passage = generate_passage(vocabulary)
            while not passage:
                passage = generate_passage(vocabulary)

            vm = vocabulary.metas.first()        
    
        
        data.update(
            {
                "translation": vocabulary.translation,
                "text": vocabulary.text,
                "description": vocabulary.description,
                "sentences": vm.sentences,
                "passage": vm.passage,
                "passage_title": vm.passage_title,
                "passage_vocabularies": vm.passage_vocabularies,
                "image": vocabulary.image.url,
                "category": vocabulary.category,
                "message": "success"
            }
        )

        return JsonResponse(data, safe=False)            


class VocabularyChartAPI(CSRFExempt, AdminRoleRequired, View):
    
    def get(self, req, *args, **kwargs):

        return JsonResponse(vocabulary_chart(req.user.organization), safe=False)


class DictionaryExamsViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherDictionaryExamsListViewAPI.as_view()
        
        return view(req, *args, **kwargs)
    
    def get(self, req, *args, **kwargs):

        delete_expired_sessions()
        
        exams = []

        for exam in DictionaryExam.objects.filter(is_training=False, organization=req.user.organization):
            
            data = {
                "id": exam.id,
                "title": exam.title,
                "author": exam.author.get_full_name(),
                "max_sessions": exam.max_sessions,
                "is_preset": exam.is_preset,
                "is_recorded": exam.is_recorded,
                "start_date": exam.start_date,
                "end_date": exam.end_date,
                "date_created": exam.date_created,
            }

            if exam.package:
                data["pacakage"] = exam.package.title
            
            exams.append(data)
        
        return JsonResponse(exams, safe=False)


class DictionaryExamDetailViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        if req.user.role in ('teacher', 'supervisor'):
            view = StudentDictionaryExamDetailViewAPI.as_view()
        else:
            view = StudentDictionaryExamDetailViewAPI.as_view()
        
        return view(req, *args, **kwargs)
    

    def get(self, req, pk, *args, **kwargs):

        exam = get_object_or_404(DictionaryExam, id=pk)
        
            
        data = {
            "id": exam.id,
            "title": exam.title,
            "package": None,
            "author": exam.author.get_full_name(),
            "max_sessions": exam.max_sessions,
            "is_preset": exam.is_preset,
            "is_recorded": exam.is_recorded,
            "package_source": exam.package_source,
            "start_date": exam.start_date,
            "end_date": exam.end_date,
            "date_created": exam.date_created,
            "participated": False
        }

        exam_session = check_participation(req.user, exam)
        if exam_session:
            data.update({
                "participated": True,
                "exam_session": {
                    "package": exam_session.package.title,
                    "is_successful": exam_session.is_successful,
                    "points": exam_session.points
                }
            })


        if exam.package:
            data["package"] = exam.package.title
            
        return JsonResponse(data, safe=False)


    def delete(self, req, pk, *args, **kwargs):

        exam = get_object_or_404(DictionaryExam, id=pk)

        data = {
            "message": "failed",
            "errors": []
        }

        if req.user.role not in ('teacher', 'supervisor'):
            data["errors"].append("role")
        
        if not (req.user == exam.author or req.user.role == 'supervisor'):
            data["errors"].append("permission")
        
        if not data["errors"]:
            exam.delete()
            data["message"] = "success"
        
        return JsonResponse(data, safe=False)


class GetOngoingExamAPI(CSRFExempt, LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):
        data = {
            "exam": None
        }

        exam_session = get_ongoing_session(req.user)
        if exam_session:
            data["exam"] = {
                "id": exam_session.exam.id,
                "title": exam_session.exam.title,
                "package": exam_session.package.title,
            }
        
        return JsonResponse(data, safe=False)


class SubmitAnswerAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        
        show_type = req.POST.get('show_type', '').strip()
        data = {
            "message": "failed",
            "errors": []
        }

        if show_type in ('0', '1'):
            test_id = req.POST.get('test_id', '0').strip()
            option_id = req.POST.get('option_id', '0').strip()

            test = VocabularyTest.objects.filter(id=test_id).first()
            option = VocabularyTestOption.objects.filter(id=option_id).first()

            if not test or not option:
                data["errors"].append("invalid-ids")

            elif delete_expired_session(test.exam_session):
                data["errors"].append("expired")
            
            if test.selected_option:
                data["errors"].append("already-submitted")
            
            if test.exam_session.tests.filter(state='none').count() == 0:
                end_exam_session(test.exam_session)
                data["errors"].append("expired")

            if not data["errors"]:
                if test.answer_option == option:
                    test.state = 'true'
                else:
                    test.state = 'false'


                test.selected_option = option
                test.save()

                if test.exam_session.tests.filter(state='none').count() == 0:
                    end_exam_session(test.exam_session)
                    data["errors"].append("expired")

                data.update(
                    {
                        "message": "success",
                        "state": test.state,
                        "selected_options": option.id,
                        "answer_option": test.answer_option.id,
                        "show_type": test.show_type
                    }
                )
                
        
        elif show_type == '2':
            test_id = req.POST.get('test_id', '0').strip()
            input_option = req.POST.get('input_option', '').strip().lower().replace('’', "'")
            input_option = re.sub(r'\s+', ' ', input_option)
            
            data = {
                "message": "failed",
                "errors": []
            }

            test = VocabularyTest.objects.filter(id=test_id).first()

            if not test or len(input_option) < 2:
                data["errors"].append("invalid-ids")

            elif delete_expired_session(test.exam_session):
                data["errors"].append("expired")
            
            if test.selected:
                data["errors"].append("already-submitted")
            
            if test.exam_session.tests.filter(state='none').count() == 0:
                end_exam_session(test.exam_session)
                data["errors"].append("expired")
            
            if not data["errors"]:
                if test.answer == input_option:
                    test.state = 'true'
                else:
                    test.state = 'false'


                test.selected = input_option
                test.save()

                if test.exam_session.tests.filter(state='none').count() == 0:
                    end_exam_session(test.exam_session)
                    data["errors"].append("expired")

                data.update(
                    {
                        "message": "success",
                        "state": test.state,
                        "selected": input_option,
                        "answer": test.answer,
                        "show_type": test.show_type
                    }
                )
                

        return JsonResponse(data, safe=False)


class DictionaryExamSessionsListAPI(LoginRequiredMixin, View):

    def get(self, req, pk, *args, **kwargs):

        delete_expired_sessions()

        exam = get_object_or_404(DictionaryExam, id=pk)
        data = [
            {
                "id": exam_session.id,
                "user": exam_session.user.get_full_name(),
                "user_id": exam_session.user.id,
                "package": exam_session.package.title,
                "is_finished": exam_session.is_finished,
                "is_successful": exam_session.is_successful,
                "is_locked": exam_session.is_locked,
                "points": exam_session.points,
                "penalty": exam_session.penalty,
            }
            for exam_session in exam.exam_sessions.order_by("-points")
        ]

        return JsonResponse(data, safe=False)


class RecordPenaltyAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        
        data = {
            "message": "failed",
            "errors": []
        }

        penalty = req.POST.get('penalty', '0').strip()

        exam_session = get_ongoing_session(req.user)

        if not exam_session:
            data["errors"].append("invalid-ids")
        
        else:
            try:
                penalty = int(penalty)
            except ValueError:
                data["errors"].append("penalty")
            
            if penalty < exam_session.penalty and not exam_session.is_penalty_reset:
                data["errors"].append("penalty")
        
        if not exam_session.is_training and exam_session.key != req.session.get(f"key{exam_session.exam.id}"):
            data["errors"].append("key")
        
        if not data["errors"]:

            if exam_session.is_penalty_reset:
                exam_session.is_penalty_reset = False
            else:
                exam_session.penalty = penalty

            exam_session.save()

            data.update(
                {
                    "message": "success",
                    "penalty": exam_session.penalty
                }
            )
            
        return JsonResponse(data, safe=False)


class ResetPenaltyAPI(CSRFExempt, AdminRoleRequired, View):

    def post(self, req, *args, **kwargs):
        
        data = {
            "message": "failed",
            "errors": []
        }

        exam_session_id = req.POST.get('exam_session_id', '0').strip()
        penalty = req.POST.get('penalty', '0').strip()

        exam_session = DictionaryExamSession.objects.filter(id=exam_session_id).first()
        if not exam_session:
            data["errors"].append("invalid-id")
        else:
            if exam_session.is_finished or exam_session.is_training:
                data["errors"].append("expired")

        try:
            penalty = int(penalty)
        except ValueError:
            data["errors"].append("penalty")


        if not data["errors"]:
            exam_session.penalty = penalty
            exam_session.is_penalty_reset = True
            exam_session.save()

            data.update(
                {
                    "message": "success",
                }
            )
            
        return JsonResponse(data, safe=False)


class LockStatusAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherLockStatusAPI.as_view()
        else:
            view = StudentLockStatusAPI.as_view()
        
        return view(req, *args, **kwargs)
    
    def get(self, req, *args, **kwargs):
        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherLockStatusAPI.as_view()
        else:
            view = StudentLockStatusAPI.as_view()
        
        return view(req, *args, **kwargs)
    

class EndExamSessionAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):
        
        data = {
            "message": "failed",
            "errors": []
        }

        exam_session = get_ongoing_session(req.user)

        if not exam_session:
            data["errors"].append("invalid-ids")
        
        if not data["errors"]:
            end_exam_session(exam_session)

            data["message"] = "success"
            
        return JsonResponse(data, safe=False)
    

class DictionaryTrainingExamsViewAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):

        duration = req.POST.get('duration', '').strip()
        package = req.POST.get('package', '').strip()

        exam_session = get_ongoing_session(req.user)

        errors = []

        if exam_session:
            errors.append("ongoing")
            errors.append({"id": exam_session.exam.id, "title": exam_session.exam.title})

        try:
            duration = int(duration)
        except ValueError:
            errors.append('duration')
        else:
            if not 9 < duration < 121:
                errors.append('duration')
        
        start_date = timezone.make_aware(datetime.now())
        end_date = start_date + timedelta(minutes=duration)
        
        try:
            package = int(package)
            is_preset = True
        except ValueError:
            errors.append('package')
        else:
            package = VocabularyPackage.objects.filter(id=package, organization=req.user.organization).first()
            if not package:
                errors.append('package')
        
        data = {"message": "failed"}

        if not errors:

            exam = DictionaryExam(
                title=package.title,
                author=req.user,
                max_sessions=1,
                is_preset=is_preset,
                is_recorded=False,
                is_training=True,
                start_date=start_date,
                end_date=end_date,
                package=package,
                created_by=package.created_by,
                package_source=package.created_by,
                organization=req.user.organization
            )

            exam.save()
            data.update(
                {
                    "message": "success",
                    "exam_id": exam.id
                }
            )

        else:
            data["errors"] = errors
        
        
        return JsonResponse(data, safe=False)


    def get(self, req, *args, **kwargs):

        delete_expired_sessions()
        
        exams = []

        for exam in DictionaryExam.objects.filter(author=req.user, is_training=True, created_by="supervisor"):
            
            data = {
                "id": exam.id,
                "title": exam.title,
                "author": exam.author.get_full_name(),
                "max_sessions": exam.max_sessions,
                "is_preset": exam.is_preset,
                "is_recorded": exam.is_recorded,
                "start_date": exam.start_date,
                "end_date": exam.end_date,
                "date_created": exam.date_created,
            }

            if exam.package:
                data["package"] = exam.package.title
            
            exams.append(data)
        
        return JsonResponse(exams, safe=False)


class RegenerateVocabularyAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, pk, *args, **kwargs):

        vocabulary = Vocabulary.objects.filter(id=pk, author=req.user).first()
        data = {
            "message": "failed",
            "errors": [],
        }

        if not vocabulary:
            data["errors"].append("not-found")

        if not data["errors"]:

            response = get_full_vocabulary(vocabulary.text)
            if not response:
                return JsonResponse(data, safe=False)
            
            vocabulary.translation=response[0].strip()
            vocabulary.description=response[2].strip()
            vocabulary.category=response[1].strip()

            if vocabulary.parent:
                Vocabulary.objects.filter(id=vocabulary.parent_id).update(
                    translation=vocabulary.translation,
                    description=vocabulary.description,
                    category=vocabulary.category,
                )
            else:
                sys_vocabulary = Vocabulary.objects.filter(text=vocabulary.text, created_by="system").first()

                if sys_vocabulary:
                    Vocabulary.objects.filter(id=sys_vocabulary.id).update(
                        translation=vocabulary.translation,
                        description=vocabulary.description,
                        category=vocabulary.category,
                    )
                else:
                    sys_vocabulary = Vocabulary(
                        text=vocabulary.text,
                        translation=vocabulary.translation,
                        description=vocabulary.description,
                        category=vocabulary.category,
                        created_by="system",
                        organization=req.user.organization
                    )
                    sys_vocabulary.save()

                vocabulary.parent = sys_vocabulary

            vocabulary.save()
        
            data["message"] = "success"
            
        return JsonResponse(data, safe=False)
