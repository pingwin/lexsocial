#!./.virtenv/bin/python
from flask import (
        Flask,
        request,
        jsonify,
        render_template,
        url_for,
        send_from_directory
        )
import datetime
import logging
from dateutil import tz
from flask.ext.pymongo import PyMongo
from flask.ext.script import Manager
from flask_admin import Admin
from models import (
        EventsView,
        GroupsView
        )

##------------------------------------------------------------------------------
## Bootstraping Flask
##------------------------------------------------------------------------------
app = Flask(
        'lexsocial',
        static_folder = 'static',
        template_folder = 'templates'
)

app.config.from_object('settings')

with app.app_context():
        app.logger.setLevel(level=
                             getattr(logging, app.config.get('LOG_LEVEL', 'DEBUG')))

mongo = PyMongo(app)
manager = Manager(app)

##------------------------------------------------------------------------------
## Admin Panel
##------------------------------------------------------------------------------
admin = Admin(app, url=app.config.get('ADMIN_URL', '/admin/'), name='LexSocial', template_mode='bootstrap3')
with app.app_context():
        admin.add_view(EventsView(mongo.db.events, 'Events'))
        admin.add_view(GroupsView(mongo.db.groups, 'Groups'))


##------------------------------------------------------------------------------
## Application Commands
##------------------------------------------------------------------------------
@manager.command
def sync_calendars():
        from sync import sync
        return sync(app, mongo)


##------------------------------------------------------------------------------
## Views
##------------------------------------------------------------------------------
@app.route("/", methods=['GET'])
def main():
        return render_template(
                'index.html',
                groups = mongo.db.groups.find()
        )

@app.route("/events", methods=['GET'])
def events_json():
        browser_tz = tz.gettz(request.args.get('browser_timezone', app.config.get('TIMEZONE')))
        
        From = datetime.datetime.fromtimestamp((int(request.args.get('from'))/1000)-86400, tz=browser_tz)
        To   = datetime.datetime.fromtimestamp((int(request.args.get('to')  )/1000)+86400, tz=browser_tz)

        return jsonify(
                success = 1,
                result =
                map(lambda x:
                    {'id'          : str(x['_id']),
                     'title'       : x['summary'],
                     'description' : x['desc'],
                     'url'         : '/event/'+str(x['_id']),
                     'bg_color'    : mongo.db.groups.find_one({'_id': x['group_id']}).get('bg_color', None),
                     'start'       : int(x['start'].replace(tzinfo=browser_tz).strftime("%s")) * 1000,
                     'end'         : int(x['end'].replace(tzinfo=browser_tz).strftime("%s")) * 1000
                     },
                    mongo.db.events.find({'start' : {'$gte' : From},
                                       'end'   : {'$lte': To}
                                       })))

@app.route('/event/<ObjectId:event_id>', methods=['GET'])
def event_details(event_id):
        return render_template(
                'event_details.html',
                event = mongo.db.events.find_one_or_404(
                        {'_id' : event_id}))

@app.route('/<any(tmpls,components,img,js,css):subdir>/<path:filename>', methods=['GET'])
def static_files(subdir, filename):
        app.logger.debug("subdir:'%s' filename:'%s'" % (subdir, filename))
        return send_from_directory('static/'+subdir, filename)


##------------------------------------------------------------------------------
## Now let'r rip!
##------------------------------------------------------------------------------
if __name__ == '__main__':
        manager.run()
