from django.contrib import admin

from dictionary.models import (
    VocabularyPackage,
    Vocabulary,
    VocabularyMeta,
    DictionaryExam,
    DictionaryExamSession,
    VocabularyTest,
    VocabularyTestOption
)

@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "author",
        "parent",
        "package",
    ]
    list_filter = [
        "created_by"
    ]

    search_fields = [
        "text",
    ]

@admin.register(VocabularyPackage)
class VocabularyPackageAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    

admin.site.register(VocabularyMeta)
admin.site.register(DictionaryExam)
admin.site.register(DictionaryExamSession)
admin.site.register(VocabularyTest)
admin.site.register(VocabularyTestOption)
