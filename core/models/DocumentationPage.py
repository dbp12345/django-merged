from django.db import models
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

class Documentation_Page(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True, unique=True, default="untitled")
    content = MarkdownxField()

    def formatted_markdown(self):
        return markdownify(self.content)

    class Meta:
        verbose_name = "Documentation: Page"
        verbose_name_plural = "Documentation: Pages"

    def __str__(self):
        return self.title or "-"