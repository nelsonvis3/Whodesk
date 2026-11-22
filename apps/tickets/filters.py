import django_filters as df

from .models import Priority, Status, Ticket


class TicketFilter(df.FilterSet):
    status = df.MultipleChoiceFilter(choices=Status.choices)
    priority = df.MultipleChoiceFilter(choices=Priority.choices)
    assigned_to = df.CharFilter(method="filter_assigned")

    class Meta:
        model = Ticket
        fields = ["status", "priority", "category", "created_by"]

    def filter_assigned(self, queryset, name, value):
        # "me" = asignados al usuario actual; "unassigned" = sin asignar; o un id numérico.
        if value == "me":
            return queryset.filter(assigned_to=self.request.user)
        if value == "unassigned":
            return queryset.filter(assigned_to__isnull=True)
        if value.isdigit():
            return queryset.filter(assigned_to_id=int(value))
        return queryset.none()
