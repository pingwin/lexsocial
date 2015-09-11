from flask import current_app
from flask.ext.script import Command

import json
import datetime
import requests
from icalendar import Calendar
from dateutil import (
    rrule,
    tz)

def _write_it(app, mongo, start, end, group, ev):
    to_utc = tz.gettz('UTC')
    start = start.replace(tzinfo=to_utc)
    end   = end.replace(tzinfo=to_utc)

    try:
        mongo.db.events.update(
            {
                'group_id' : group['_id'],
                'start'    : start,
                'end'      : end,
                'loc'      : ev.get('LOCATION', None)
            },
            {
                'group_id'      : group['_id'],
                'start'         : start,
                'end'           : end,
                'loc'           : ev.get('LOCATION', None),
                'last-modified' : ev['LAST-MODIFIED'].dt if 'LAST-MODIFIED' in ev else datetime.datetime.now(),
                'lat'           : ev['GEO'].latitude if 'GEO' in ev else None,
                'long'          : ev['GEO'].longitude if 'GEO' in ev else None,
                'status'        : ev.get('STATUS', 'CONFIRMED'),
                'summary'       : ev['SUMMARY'],
                'desc'          : ev.get('DESCRIPTION', None),
                'url'           : ev.get('URL', None),
                'iCALUID'       : ev['UID']
            },
            upsert = True
        )
    except Exception,inst:
        app.logger.exception('failed to write event %s' % str(inst))
        app.logger.error('failed to write to %s %s' % (group['name'], ev))
        raise inst

def _do_sync(app, mongo, group):
    if 'ical' not in group:
        app.logger.info('group w/o ical found :: %s' % group['name'])
        return
        
    app.logger.info("Requesting ical for %s from %s" % (group['name'], group['ical']))
    ics_raw = requests.get(group['ical']).text

    cal = Calendar.from_ical(ics_raw)

    for ev in cal.subcomponents:
        if 'DTSTART' not in ev:
            app.logger.debug('found non-event of type %s in calendar for %s' % (type(ev), group['name']))
            continue
        app.logger.debug('found event for %s title = %s' % (group['name'], ev['SUMMARY']))

        dtstart = ev['DTSTART'].dt
        dtend   = ev['DTEND'].dt
        
        if type(dtstart) == datetime.date:
            dtstart = datetime.datetime(dtstart.year, dtstart.month, dtstart.day)
        
        if type(dtend) == datetime.date:
            dtend   = datetime.datetime(dtend.year, dtend.month, dtend.day)       

        if 'RRULE' not in ev:
            _write_it(
                app,
                mongo,
                start = dtstart,
                end   = dtend,
                group = group,
                ev    = ev
                )                    
        else:
            limit = datetime.datetime.now(dtstart.tzinfo)+ datetime.timedelta(days=365.25*2)
            diff = dtend - dtstart
            for starts in filter(lambda x: limit > x,
                                 rrule.rrulestr(
                                     ev['RRULE'].to_ical(),
                                     dtstart = dtstart
                                 )
               ):
                app.logger.debug('inserting recurring event for %s title %s on %s' % (
                    group['name'],
                    ev['SUMMARY'],
                    starts))
                _write_it(
                    app,
                    mongo,
                    start = starts,
                    end   = starts + diff,
                    group = group,
                    ev    = ev
                    )
                

def sync(app, mongo):
    for group in mongo.db.groups.find():
        try:
            _do_sync(app, mongo, group)
        except Exception, inst:
            app.logger.exception("Fatal error importing %s" % group['name'])

