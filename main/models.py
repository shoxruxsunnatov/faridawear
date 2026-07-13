from django.db import (
    models,
    transaction
)


class Organization(models.Model):
    title = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} {self.date_created}'


class SystemVariable(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="system_variables"
    )

    key = models.CharField(max_length=100)
    value = models.BigIntegerField(default=0)

    @classmethod
    def next_value(cls, organization, key):
        with transaction.atomic():
            var = (
                cls.objects
                .select_for_update()
                .get(
                    organization=organization,
                    key=key,
                )
            )

            var.value += 1
            var.save(update_fields=["value"])

            return var.value


class Group(models.Model):
    title = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, related_name='groups', on_delete=models.CASCADE)
    cross_id = models.IntegerField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} {self.date_created}'

