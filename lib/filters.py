# coding: utf-8
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.filters import FieldListFilter
from django.db.models.fields import IntegerField, AutoField

from django.contrib.admin import ListFilter
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _


# 多选过滤
class MultipleSelectFieldListFilter(FieldListFilter):

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = '%s_filter' % field_path
        self.filter_statement = '%s__id' % field_path
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)
        self.lookup_choices = field.get_choices(include_blank=False)
        super(MultipleSelectFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def values(self):
        """
        Returns a list of values to filter on.
        """
        values = []
        value = self.used_parameters.get(self.lookup_kwarg, None)
        if value:
            values = value.split(',')
        # convert to integers if IntegerField
        if type(self.field.model._meta.pk) in [IntegerField, ]:
            values = [int(x) for x in values]
        return values

    def queryset(self, request, queryset):
        raise NotImplementedError

    def choices(self, cl):
        # from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
        yield {
            'selected': self.lookup_val is None,
            'query_string': cl.get_query_string({},
                [self.lookup_kwarg]),
            'display': _('All')
        }
        for pk_val, val in self.lookup_choices:
            selected = pk_val in self.values()
            pk_list = set(self.values())
            if selected:
                pk_list.remove(pk_val)
            else:
                pk_list.add(pk_val)
            queryset_value = ','.join([str(x) for x in pk_list])
            if pk_list:
                query_string = cl.get_query_string({
                    self.lookup_kwarg: queryset_value,
                    })
            else:
                query_string = cl.get_query_string({}, [self.lookup_kwarg])
            yield {
                'selected': selected,
                'query_string': query_string,
                'display': val,
            }


class IntersectionFieldListFilter(MultipleSelectFieldListFilter):
    """
    A FieldListFilter which allows multiple selection of
    filters for many-to-many type fields. A list of objects will be
    returned whose m2m contains all the selected filters.
    """

    def queryset(self, request, queryset):
        for value in self.values():
            filter_dct = {
                self.filter_statement: value
            }
            queryset = queryset.filter(**filter_dct)
        return queryset


class UnionFieldListFilter(MultipleSelectFieldListFilter):
    """
    A FieldListFilter which allows multiple selection of
    filters for many-to-many type fields. A list of objects will be
    returned whose m2m contains all the selected filters.
    """

    def queryset(self, request, queryset):
        filter_statement = "%s__in" % self.filter_statement
        filter_statement = filter_statement.replace('__id', '')
        filter_values = self.values()
        filter_dct = {
            filter_statement: filter_values
        }

        if filter_values:
            return queryset.filter(**filter_dct)
        else:
            return queryset


# 输入框过滤
class SingleTextInputFilter(ListFilter):
    """
    renders filter form with text input and submit button
    """
    parameter_name = None
    template = "admin/textinput_filter.html"

    def __init__(self, request, params, model, model_admin):
        super(SingleTextInputFilter, self).__init__(
            request, params, model, model_admin)
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify "
                "a 'parameter_name'." % self.__class__.__name__)

        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value

    def value(self):
        """
        Returns the value (in string format) provided in the request's
        query string for this filter, if any. If the value wasn't provided then
        returns None.
        """
        return self.used_parameters.get(self.parameter_name, None)

    def has_output(self):
        return True

    def expected_parameters(self):
        """
        Returns the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        return [self.parameter_name]


    def choices(self, cl):
        all_choice = {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self.parameter_name]),
            'display': _('All'),
        }
        return ({
            'get_query': cl.params,
            'current_value': self.value(),
            'all_choice': all_choice,
            'parameter_name': self.parameter_name
        }, )

# 两个输入框
class DoubleTextInputFilter(ListFilter):
    """
    renders filter form with text input and submit button
    """
    parameter_name = None

    template = "admin/doubletextinput_filter.html"

    def __init__(self, request, params, model, model_admin):
        super(DoubleTextInputFilter, self).__init__(
            request, params, model, model_admin)
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify "
                "a 'parameter_name'." % self.__class__.__name__)

        if self.parameter_name[0] in params:
            value = params.pop(self.parameter_name[0])
            self.used_parameters[self.parameter_name[0]] = value
        if self.parameter_name[1] in params:
            value = params.pop(self.parameter_name[1])
            self.used_parameters[self.parameter_name[1]] = value

    def value(self):
        """
        Returns the value (in string format) provided in the request's
        query string for this filter, if any. If the value wasn't provided then
        returns None.
        """
        value = []
        value.append(self.used_parameters.get(self.parameter_name[0], None))
        value.append(self.used_parameters.get(self.parameter_name[1], None))
        return value

    def has_output(self):
        return True

    def expected_parameters(self):
        """
        Returns the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        return [self.parameter_name]


    def choices(self, cl):
        all_choice = {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, self.parameter_name),
            'display': _('All'),
        }
        return ({
            'get_query': cl.params,
            'current_value': self.value(),
            'all_choice': all_choice,
            'parameter_name': self.parameter_name
        }, )

