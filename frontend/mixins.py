from django.core.exceptions import PermissionDenied


class HomePagePermissionMixin:

    def dispatch(self, request, *args, **kwargs):
        pass


class ContextMixin:
    title = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context