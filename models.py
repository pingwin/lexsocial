#from main import app, mongo, admin
from flask_admin.contrib.pymongo import ModelView
from wtforms import form, fields

class GroupForm(form.Form):
    name     = fields.TextField('Name')
    slab     = fields.TextField('SLAB')
    bg_color = fields.TextField('Small Icon BG-Color')
    www      = fields.TextField('WWW')
    ical     = fields.TextField('iCal')

class GroupsView(ModelView):
    column_list = ('name', 'slab', 'bg_color')
    column_sortable_list = ('name',)
    form = GroupForm


class EventForm(form.Form):
    status = fields.SelectField('Status',
                                choices = [('CONFIRMED', 'Confirmed'), ('NOTCONFIRMED', 'Not Confirmed')])
    url    = fields.TextField('URL')
    summary = fields.TextField('Summary')
    start   = fields.DateTimeField('Start')
    end     = fields.DateTimeField('End')
    
    desc   = fields.TextAreaField('Description')
    


class EventsView(ModelView):
    column_list = ('start', 'end', 'summary', 'group')
    column_sortable_list = ('start', 'end', 'group')

    form = EventForm
