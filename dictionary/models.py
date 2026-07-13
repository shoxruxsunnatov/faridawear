import os

from django.db import models

from account.models import User
from main.models import Organization

from main.variables import (
    USER_ROLES,
    TEST_LINK_STATE_CHOICE,
    TEST_SHOW_TYPE_CHOICE,
    TEST_PART_CHOICE,
    VOCABULARY_TYPE_CHOICE
)
from main.utils import (
    get_random_index,
    generate_image_filename

)


class VocabularyPackage(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, related_name="vocabulary_packages", on_delete=models.SET_NULL, null=True)

    created_by = models.CharField(max_length=30, choices=USER_ROLES)
    date_created = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(Organization, related_name="vocabulary_packages", on_delete=models.CASCADE)

    class Meta:
        ordering = ["date_created"]

    def __str__(self):
        return f"{self.title} | {self.author}"


class Vocabulary(models.Model):
    author = models.ForeignKey(
        User,
        related_name="vocabularies",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children"
    )
    package = models.ForeignKey(
        VocabularyPackage,
        related_name="vocabularies",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    text = models.CharField(max_length=200)
    translation = models.CharField(max_length=200)
    image = models.ImageField(upload_to=generate_image_filename, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=30, choices=VOCABULARY_TYPE_CHOICE)

    is_test_available = models.BooleanField(default=0)
    created_by = models.CharField(max_length=30, choices=USER_ROLES)
    date_created = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(Organization, related_name="vocabularies", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'Vocabularies'
        ordering = ["text"]

    def __str__(self):
        return f"{self.text} | {self.author}"
    
    def delete(self, **kwargs):
        if self.image:
            os.remove(self.image.path)
            
        super().delete(**kwargs)


class VocabularyMeta(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, related_name="metas", on_delete=models.CASCADE, null=True)
    sentences = models.JSONField(null=True, blank=True)
    passage = models.TextField(null=True, blank=True)
    passage_title = models.CharField(max_length=200, null=True, blank=True)
    passage_vocabularies = models.JSONField(null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_created"]

    def __str__(self):
        return f"{self.vocabulary}"


class DictionaryExam(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    author = models.ForeignKey(User, related_name='dictionary_exams', on_delete=models.SET_NULL, null=True, blank=True)
    package = models.ForeignKey(VocabularyPackage, related_name='dictionary_exams', on_delete=models.CASCADE, null=True, blank=True)
    max_sessions = models.PositiveIntegerField()

    is_preset = models.BooleanField()
    is_recorded = models.BooleanField()
    is_training = models.BooleanField()
    package_source = models.CharField(max_length=30, choices=USER_ROLES)
    created_by = models.CharField(max_length=30, choices=USER_ROLES)
    organization = models.ForeignKey(Organization, related_name="dictionary_exams", on_delete=models.SET_NULL, null=True, blank=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} -> {self.author.username}"


class DictionaryExamSession(models.Model):
    user = models.ForeignKey(User, related_name='dictionary_exam_sessions', on_delete=models.CASCADE)
    exam = models.ForeignKey(DictionaryExam, related_name='exam_sessions', on_delete=models.CASCADE)
    package = models.ForeignKey(VocabularyPackage, related_name='exam_sessions', on_delete=models.CASCADE)

    is_recorded = models.BooleanField()
    is_training = models.BooleanField()
    is_finished = models.BooleanField(default=False)
    is_successful = models.BooleanField(default=False)
    is_penalty_reset = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_lock_reset = models.BooleanField(default=False)
    
    points = models.IntegerField(default=0)
    penalty = models.PositiveIntegerField(default=0)
    key = models.CharField(max_length=10, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.package.title} -> {self.user.username}"


class VocabularyTest(models.Model):
    exam_session = models.ForeignKey(DictionaryExamSession, related_name='tests', on_delete=models.CASCADE)
    vocabulary = models.ForeignKey(Vocabulary, related_name='tests', on_delete=models.CASCADE)
    answer_option = models.ForeignKey("VocabularyTestOption", related_name='tests', null=True, blank=True, on_delete=models.CASCADE)
    selected_option = models.ForeignKey("VocabularyTestOption", related_name='vocabulary_test', blank=True, null=True, on_delete=models.SET_NULL)
    hint = models.CharField(max_length=200, null=True, blank=True,)
    answer = models.CharField(max_length=200, null=True, blank=True,)
    selected = models.CharField(max_length=200, null=True, blank=True,)
    state = models.CharField(max_length=10, choices=TEST_LINK_STATE_CHOICE, default='none')
    show_type = models.CharField(max_length=10, choices=TEST_SHOW_TYPE_CHOICE)
    part = models.CharField(max_length=10, choices=TEST_PART_CHOICE)

    random_index = models.IntegerField(default=get_random_index)

    class Meta:
        ordering = ['id']


class VocabularyTestOption(models.Model):
    text = models.TextField()
    test = models.ForeignKey(VocabularyTest, related_name='options', on_delete=models.CASCADE)

