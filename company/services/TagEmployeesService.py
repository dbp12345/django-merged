from typing import Optional, List, Tuple
from django.db import transaction, IntegrityError
from company.models import Tag, Employees


class TagEmployeesService:
    @staticmethod
    def attach_tag_to_employee(employee: Optional["Employees"], tag_name: Optional[str]) -> Tuple[Optional["Tag"], bool]:
        """
        Attach tag to employee. Create tag if missing.
        Returns (tag, created). If input is empty or employee not persisted — returns (None, False).
        """
        # ignore empty inputs instead of crashing
        if not employee:
            return None, False
        if not tag_name or not tag_name.strip():
            return None, False

        # ensure employee is saved — can't add M2M on unsaved instance
        if not getattr(employee, "pk", None):
            return None, False

        tag_name = tag_name.strip()

        print("tag_name:", tag_name)

        tag: Optional[Tag] = None
        created: bool = False

        try:
            with transaction.atomic():
                tag, created = Tag.objects.get_or_create(
                    name=tag_name
                )
        except IntegrityError:
            # race: someone else created the tag concurrently
            tag = Tag.objects.filter(name=tag_name).first()
            if tag is None:
                # last attempt to create — handle another possible race
                try:
                    tag = Tag.objects.create(name=tag_name)
                    created = True
                except IntegrityError:
                    tag = Tag.objects.filter(name=tag_name).first()
                    created = False
            else:
                created = False

        if tag is None:
            return None, False

        # attach (idempotent)
        employee.tags.add(tag)
        return tag, created

    @staticmethod
    def replace_tags_for_employee(employee: Optional["Employees"], tag_names: Optional[List[str]]) -> Tuple[List["Tag"], int]:
        """
        Replace all tags for employee with provided list of tag names.
        Returns (tags, created_count).
        """
        if not employee:
            return [], 0
        if not getattr(employee, "pk", None):
            return [], 0

        # normalize and dedupe names
        names: List[str] = []
        if tag_names:
            for n in tag_names:
                if n is None:
                    continue
                s = str(n).strip()
                if s and s not in names:
                    names.append(s)

        # if empty list provided -> remove all tags
        if not names:
            employee.tags.clear()
            return [], 0

        tags: List["Tag"] = []
        created_count = 0

        # create/get tags (simple race-safe fallback)
        for name in names:
            try:
                tag, was_created = Tag.objects.get_or_create(name=name)
            except IntegrityError:
                tag = Tag.objects.filter(name=name).first()
                if tag is None:
                    try:
                        tag = Tag.objects.create(name=name)
                        was_created = True
                    except IntegrityError:
                        tag = Tag.objects.filter(name=name).first()
                        was_created = False
                else:
                    was_created = False
            tags.append(tag)
            if was_created:
                created_count += 1

        # replace M2M in one atomic operation
        with transaction.atomic():
            employee.tags.set(tags)

        return tags, created_count
