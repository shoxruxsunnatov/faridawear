import enchant
from random import shuffle, sample, choice
from math import ceil
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Sum
from collections import defaultdict

from django.db.models import Count
from django.db.models.functions import TruncDate
    
from account.models import User
from dictionary.models import (
    Vocabulary,
    VocabularyPackage,
    VocabularyTest,
    VocabularyTestOption,
    DictionaryExam,
    DictionaryExamSession
)
from students.models import Record


def check_text(text) -> dict:
    us = enchant.Dict("en_US")
    uk = enchant.Dict("en_UK")
    en = enchant.Dict("en")
    data = {}

    for word in text.split():
        if not (us.check(word) or uk.check(word)):
            data[word] = en.suggest(word)[:5]
    
    return data


def vocabulary_chart(organization) -> dict:
    now = timezone.now().date()
    start_date = now - timedelta(days=30)

    results = (
        Vocabulary.objects.filter(
            organization=organization,
            date_created__date__gte=start_date,
        )
        .annotate(day=TruncDate("date_created"))
        .values("day", "created_by")
        .annotate(total=Count("id"))
    )

    counts = defaultdict(dict)
    for row in results:
        counts[row["day"]][row["created_by"]] = row["total"]

    labels = []
    student_values = []
    system_values = []

    for i in range(31):
        day = start_date + timedelta(days=i)

        labels.append(day)
        student_values.append(counts[day].get("student", 0))
        system_values.append(counts[day].get("system", 0))

    return {
        "labels": labels,
        "student_values": student_values,
        "system_values": system_values,
    }


def end_exam_session(exam_session: DictionaryExamSession) -> DictionaryExamSession:
    exam_session.points = exam_session.tests.filter(state='true').count()
    exam_session.is_finished = True
    exam_session.points = 0 if exam_session.points - exam_session.penalty < 0 else exam_session.points - exam_session.penalty
    exam_session.is_successful = True if exam_session.points >= 97 else False
    exam_session.save()

    user = exam_session.user

    if exam_session.is_recorded:
        record = Record.objects.filter(user=user, package=exam_session.package).first()
        if record and exam_session.points > record.points:
            record.delete()
            record = None
        
        if not record:
            record = Record(
                user=user,
                package=exam_session.package,
                points=exam_session.points,
                level='0',
                is_successful=exam_session.is_successful,
                data_type='dictionary'
            )
            record.save()
        
        aggregate_result = user.records.filter(is_successful=True).aggregate(total_points=Sum("points"))
        user.rating = aggregate_result["total_points"] or 0
        user.save()

    return exam_session


def delete_expired_sessions() -> None:
    now = timezone.make_aware(datetime.now())
    exam_sessions = DictionaryExamSession.objects.filter(end_date__lte=now, is_finished=False)
    for exam_session in exam_sessions:
        end_exam_session(exam_session)


def delete_expired_session(exam_session: DictionaryExamSession) -> bool:
    now = timezone.make_aware(datetime.now())
    if exam_session.end_date <= now:
        end_exam_session(exam_session)
        return True
    else:
        return False


def get_ongoing_session(user: User) -> DictionaryExamSession:
    delete_expired_sessions()

    return user.dictionary_exam_sessions.filter(is_finished=False).first()
    

def check_participation(user: User, exam: DictionaryExam) -> DictionaryExamSession:
    exam_session = exam.exam_sessions.filter(user=user, is_finished=True).first()

    return exam_session if exam_session else False


def delete_expired_exams() -> None:
    now = timezone.make_aware(datetime.now())
    DictionaryExam.objects.filter(end_date__lte=now - timedelta(days=2)).delete()
    DictionaryExam.objects.filter(is_training=True, end_date__lte=now - timedelta(hours=6)).delete()


def check_packages(package: VocabularyPackage) -> bool:

    if package.created_by == "supervisor":
        packages = list(
            VocabularyPackage.objects.filter(created_by=package.created_by, organization=package.organization).order_by('date_created')
        )
    elif package.created_by == "student":
        packages = list(
            VocabularyPackage.objects.filter(author=package.author, created_by=package.created_by).order_by('date_created')
        )

    index = packages.index(package)
    packages = packages[:index + 1]

    for i in packages:
        if i.vocabularies.count() < 50:
            return False
    
    return packages, index


def generate(packages: list, index: int) -> list:

    package = packages[index]
    packages = packages[:index]

    vocabularies = list(package.vocabularies.all())
    vocabulary_options = []

    if index == 0:
        vocabularies.extend(vocabularies)
        vocabulary_options = vocabularies.copy()
        
    elif 0 < index < 50:
        per_package = ceil(50 / index)
        spare_list = []
        spare_needed = 50 % index


        if spare_needed > 0:
            for i in packages:
                all_vocabularies = list(i.vocabularies.all())
                sample_list = sample(all_vocabularies, k=per_package)
                vocabularies.extend(sample_list[:-1])
                spare_list.append(sample_list[-1])

                vocabulary_options.extend(all_vocabularies)
            
            vocabularies.extend(sample(spare_list, k=spare_needed))
        
        else:
            for i in packages:
                all_vocabularies = list(i.vocabularies.all())
                vocabularies.extend(
                    sample(all_vocabularies, k=per_package)
                )

                vocabulary_options.extend(all_vocabularies)

    else:
        packages = sample(packages, k=50)
        for i in packages:
            vocabularies.append(
                choice(list(i.vocabularies.all()))
            )
    
    
    return vocabularies, vocabulary_options


def generate_choice_test(
    exam_session: DictionaryExamSession,
    vocabularies: list[Vocabulary],
    vocabulary_options: list[Vocabulary],
    part: str
    ) -> None:

    if part == '1':
        vocabularies = vocabularies[:50]
    elif part == '2':
        vocabularies = vocabularies[50:]
    else:
        vocabularies.clear()
    
    # for vocabulary in vocabularies[:5]:
    #     test = VocabularyTest(
    #         exam_session=exam_session,
    #         vocabulary=vocabulary,
    #         show_type='0', # English to Uzbek
    #         part=part
    #     )
    #     test.save()

    #     sample_options = sample(vocabulary_options, k=3)
    #     while vocabulary in sample_options:
    #         sample_options = sample(vocabulary_options, k=3)

    #     for vocabulary_option in sample_options:
    #         option = VocabularyTestOption(
    #             test=test,
    #             text=vocabulary_option.translation # English to Uzbek
    #         )
    #         option.save()

    #     answer_option = VocabularyTestOption(
    #         test=test,
    #         text=vocabulary.translation # English to Uzbek
    #     )
    #     answer_option.save()
        
    #     test.answer_option = answer_option
    #     test.save()
        

    for vocabulary in vocabularies[0:50]:
        test = VocabularyTest(
            exam_session=exam_session,
            vocabulary=vocabulary,
            show_type='1', # Uzbek to English
            part=part
        )
        test.save()

        sample_options = sample(vocabulary_options, k=3)
        while vocabulary in sample_options:
            sample_options = sample(vocabulary_options, k=3)

        for vocabulary_option in sample_options:
            option = VocabularyTestOption(
                test=test,
                text=vocabulary_option.text # Uzbek to English
            )
            option.save()
        
        answer_option = VocabularyTestOption(
            test=test,
            text=vocabulary.text # Uzbek to English
        )
        answer_option.save()

        test.answer_option = answer_option
        test.save()


def create_hint(words: str) -> str:
    hints = [
        f"{('• ' * (len(word) - 2))}{word[-2]} •" if len(word) > 1 else '•'
        for word in words.split()
    ]
    return '   '.join(hints)


def generate_hidden_test(
    exam_session: DictionaryExamSession,
    vocabularies: list[Vocabulary],
    part: str
    ) -> None:

    if part == '1':
        vocabularies = vocabularies[:50]
    elif part == '2':
        vocabularies = vocabularies[50:]
    else:
        vocabularies.clear()


    for vocabulary in vocabularies[70:]:
        test = VocabularyTest(
            exam_session=exam_session,
            vocabulary=vocabulary,
            answer=vocabulary.text,
            hint=create_hint(vocabulary.text),
            show_type='2', # Hidden
            part=part
        )
        test.save()


def load_tests(exam_session: DictionaryExamSession) -> list:

    tests_list = []

    tests = exam_session.tests.order_by('part', 'random_index')
    for test in tests:
        if test.show_type == '0':
            options = [
                {
                    "id": option.id,
                    "text": option.text
                }
                for option in test.options.all()
            ]

            tests_list.append(
                {
                    "id": test.id,
                    "text": test.vocabulary.text, # English to Uzbek
                    "options": options,
                    "selected_option": test.selected_option.id if test.selected_option else None,
                    "state": test.state,
                    "show_type": 0,
                    "part": test.part
                }
            )
        
        elif test.show_type == '1':
            options = [
                {
                    "id": option.id,
                    "text": option.text
                }
                for option in test.options.all()
            ]

            tests_list.append(
                {
                    "id": test.id,
                    "text": test.vocabulary.translation, # Uzbek to English
                    "options": options,
                    "selected_option": test.selected_option.id if test.selected_option else None,
                    "state": test.state,
                    "show_type": 0,
                    "part": test.part
                }
            )

        elif test.show_type == '2':
            tests_list.append({
                "id": test.id,
                "text": test.vocabulary.translation,
                "hint": test.hint,
                "selected": test.selected,
                "state": test.state,
                "show_type": 2,
                "part": test.part
            })
    

    return tests_list


def generate_session_key() -> str:
    chars = 'qwertyuiopasdfghjklzxcvbnm'
    chars += chars.upper()

    key = sample(chars, k=4)

    return ''.join(key)

