from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from tags_input import fields

class CustomTagsInputField(fields.TagsInputField):

    def clean(self, value):
        mapping = self.get_mapping()
        fields = mapping['fields']
        filter_func = mapping['filter_func']
        join_func = mapping['join_func']
        split_func = mapping['split_func']

        values = dict(
            join_func(v)[::-1] for v in self.queryset
            .filter(**filter_func(value))
            .values('pk', *fields)
        )
        values = dict((k.lower(), v) for k, v in values.items())
        missing = [v for v in value if v.lower() not in values]
        if missing:
            if mapping['create_missing']:
                for v in value:
                    if v in missing:
                        if not re.match('^[a-zA-Z0-9-]+$', v):
                            raise ValidationError(
                                'Only alphanumeric and "-" characters are allowed for tag.',
                                code='invalid_alphanumeric',
                                params={'value': v},
                            )
                        o = self.queryset.model(**split_func(v))
                        o.clean()
                        o.save()
                        values[v.lower()] = o.pk
            else:
                raise ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice',
                    params={'value': ', '.join(missing)},
                )

        ids = []
        for v in value:
            ids.append(values[v.lower()])

        return forms.ModelMultipleChoiceField.clean(self, ids)

