from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)

    company_contract = models.FileField(
        upload_to="companies/contracts/",
        null=True,
        blank=True,
        help_text="Uploaded or generated company contract PDF.",
    )

    # 🔹 NEW FIELDS
    date = models.DateField(null=True, blank=True)
    text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
