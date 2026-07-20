from datetime import datetime, timedelta

from django.views.generic import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from main.models import Group
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
)
from payment.utils import charge_group_tuition

