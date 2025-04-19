from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags import humanize
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .forms import TicketForm
from .lib import format_time_spent
from .models import Company, CustomField, FollowUp, FollowUpAttachment, Ticket
from .user import HelpdeskUser
from .update_ticket import update_ticket

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'company_id', 'feedback_url', 'created_at')

class DatatablesTicketSerializer(serializers.ModelSerializer):
    """
    A serializer for the Ticket model, returns data in the format as required by
    datatables for ticket_list.html. Called from staff.datatables_ticket_list.
    """
    ticket = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    submitter = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    due_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    row_class = serializers.SerializerMethodField()
    time_spent = serializers.SerializerMethodField()
    queue = serializers.SerializerMethodField()
    kbitem = serializers.SerializerMethodField()
    submitted_from_url = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    submitter_username = serializers.SerializerMethodField()
    submitter_phone = serializers.SerializerMethodField()
    ticket_type = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        # fields = '__all__'
        fields = ('ticket', 'id', 'priority', 'title', 'queue', 'status',
                  'created', 'due_date', 'assigned_to', 'submitter', 'row_class',
                  'time_spent', 'kbitem', 'submitted_from_url', 'company',
                  'submitter_username', 'submitter_phone', 'ticket_type')

    def get_queue(self, obj):
        return {"title": obj.queue.title, "id": obj.queue.id}

    def get_ticket(self, obj):
        return str(obj.id) + " " + obj.ticket

    def get_status(self, obj):
        return obj.get_status

    def get_created(self, obj):
        return humanize.naturaltime(obj.created)

    def get_due_date(self, obj):
        return humanize.naturaltime(obj.due_date)

    def get_assigned_to(self, obj):
        if obj.assigned_to:
            if obj.assigned_to.get_full_name():
                return obj.assigned_to.get_full_name()
            elif obj.assigned_to.email:
                return obj.assigned_to.email
            else:
                return obj.assigned_to.username
        else:
            return "None"

    def get_submitter(self, obj):
        return obj.submitter_email

    def get_time_spent(self, obj):
        return format_time_spent(obj.time_spent)

    def get_row_class(self, obj):
        return obj.get_priority_css_class

    def get_kbitem(self, obj):
        return obj.kbitem.title if obj.kbitem else "not available"
    
    def get_submitted_from_url(self, obj):
        return obj.submitted_from_url if obj.submitted_from_url else "not available"

    def get_company(self, obj):
        return obj.company.name if obj.company else "Unknown"
    
    def get_submitter_username(self, obj):
        return obj.get_submitter_username()

    def get_submitter_phone(self, obj):
        return obj.get_submitter_phone()

    def get_ticket_type(self, obj):
        return obj.get_ticket_type_display()

class FollowUpAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUpAttachment
        fields = ('id', 'followup', 'file', 'filename', 'mime_type', 'size')


class FollowUpSerializer(serializers.ModelSerializer):
    followupattachment_set = FollowUpAttachmentSerializer(
        many=True, read_only=True)
    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = FollowUp
        fields = (
            'id', 'ticket', 'user', 'title', 'comment', 'public', 'new_status',
            'time_spent', 'attachments', 'followupattachment_set', 'date', 'message_id',
        )

    def create(self, validated_data):
        if validated_data["user"]:
            user = validated_data["user"]
        else:
            user = self.context['request'].user
        return update_ticket(
            user=user,
            ticket=validated_data["ticket"],
            title=validated_data.get("title", None),
            comment=validated_data.get("comment", ""),
            files=validated_data.get("attachments", None),
            public=validated_data.get("public", False),
            new_status=validated_data.get("new_status", None),
            time_spent=validated_data.get("time_spent", None),
        )


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'username', 'email', 'password')

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.is_active = True
        user.set_password(validated_data['password'])
        user.save()
        return user


class BaseTicketSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add custom fields
        for field in CustomField.objects.all():
            self.fields['custom_%s' % field.name] = field.build_api_field()


class PublicTicketListingSerializer(BaseTicketSerializer):
    """
    A serializer to be used by the public API for listing tickets. Don't expose private fields here!
    """
    ticket = serializers.SerializerMethodField()
    submitter = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    due_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    queue = serializers.SerializerMethodField()
    kbitem = serializers.SerializerMethodField()
    secret_key = serializers.CharField(read_only=True)

    class Meta:
        model = Ticket
        # fields = '__all__'
        fields = ('ticket', 'id', 'title', 'queue', 'status',
                  'created', 'due_date', 'submitter', 'kbitem', 'secret_key')

    def get_queue(self, obj):
        return {"title": obj.queue.title, "id": obj.queue.id}

    def get_ticket(self, obj):
        return str(obj.id) + " " + obj.ticket

    def get_status(self, obj):
        return obj.get_status

    def get_created(self, obj):
        return humanize.naturaltime(obj.created)

    def get_due_date(self, obj):
        return humanize.naturaltime(obj.due_date)

    def get_submitter(self, obj):
        return obj.submitter_email

    def get_kbitem(self, obj):
        return obj.kbitem.title if obj.kbitem else ""


class TicketSerializer(BaseTicketSerializer):
    followup_set = FollowUpSerializer(many=True, read_only=True)
    attachment = serializers.FileField(write_only=True, required=False)
    company = CompanySerializer(read_only=True)
    company_id = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Ticket
        fields = (
            'id', 'queue', 'title', 'description', 'resolution', 'submitter_email', 'assigned_to', 'status', 'on_hold',
            'priority', 'due_date', 'merged_to', 'attachment', 'followup_set', 'company', 'company_id', 'submitted_from_url'
        )

    def create(self, validated_data):
        company_id = validated_data.pop('company_id')
        try:
            company = Company.objects.get(company_id=company_id)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company_id": f"Company with ID '{company_id}' does not exist."})
        
        """ Use TicketForm to validate and create ticket """
        data = validated_data.copy()
        data['body'] = data['description']
        data['queue'] = data['queue'].id
        if data.get('assigned_to'):
            data['assigned_to'] = data['assigned_to'].id
        if data.get('merged_to'):
            data['merged_to'] = data['merged_to'].id

        files = {'attachment': data.pop('attachment', None)}
        queues = HelpdeskUser(self.context['request'].user).get_queues()
        queue_choices = [(q.id, q.title) for q in queues]

        # TicketForm needs id for ForeignKey (not the instance themselves)
        ticket_form = TicketForm(data=data, files=files, queue_choices=queue_choices)
        if ticket_form.is_valid():
            # ticket = ticket_form.save(user=self.context['request'].user)
            ticket = ticket_form.save(commit=False)  # Don’t save to DB yet
            ticket.company = company
            # ticket.save()
            ticket.save(user=self.context['request'].user)
            ticket.set_custom_field_values()
            print(f"Company ID received: {company_id}, Company object: {company}")
            return ticket

        raise serializers.ValidationError(ticket_form.errors)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.save_custom_field_values(validated_data)
        return instance
    

