import datetime
import os
import pickle
import re

import requests
from lxml import html

COOKIE_PATH = os.environ.get('ELEVCENTRALEN_COOKIE_PATH')
if not COOKIE_PATH:
    COOKIE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cookie')
BASE_URL = 'https://www.elevcentralen.se/en'
RE_WS = re.compile(r'\s+')


def check_ok(response, *_, **__):
    if not response:
        raise Exception(f'{response.reason}: {response.text}')


def cleanup_booking(booking):
    """
    Extract teacher and parse times into datetimes
    """
    booking.update(
        teacher=RE_WS.sub(' ', booking['employees'][0]['name'].strip()),
        start=datetime.datetime.fromisoformat(booking['start']),
        end=datetime.datetime.fromisoformat(booking['end']),
    )
    return booking


def most_recent_sunday():
    """
    Return the most recent sunday to today's date
    """
    d = datetime.date.today()
    week_day = d.isoweekday()
    if week_day != 7:
        d -= datetime.timedelta(days=week_day)
    return d


def booking_available(booking):
    return booking['isPersonBookable']


class ElevCentralen():
    def __init__(self, person_id):
        self.session = requests.Session()
        self.session.hooks['response'].append(check_ok)
        self.person_id = person_id

    def authenticate(self, username, password):
        try:
            # Load old cookies
            with open(COOKIE_PATH, 'rb') as f:
                cookies = pickle.load(f)
            self.session.cookies.update(cookies)
            if not self.session.head(BASE_URL).is_redirect:
                print('Cookie ok!')
                # Main page loads fine, cookie must be ok!
                return
            print('Cookie not ok!')
            self.session.cookies.clear()
        except (IOError, EOFError):
            # File didn't exist or was not pickled
            pass

        # No cookie, we need to login
        # 1. Get login page to grab csrf token
        # 2. Authenticate with clear text password
        # 3. Double check that login worked
        # 4. Store cookie for future use
        index_page = self.session.get(f'{BASE_URL}/Login/Index')
        tree = html.fromstring(index_page.content)

        # Get the value tag of first element with name attribute '__RequestVerificationToken' and
        # value tag
        csrf_token = tree.xpath('(//*[@name="__RequestVerificationToken" and @value]/@value)[1]')[0]

        # Login
        self.session.post(f'{BASE_URL}/Login/Authenticate', data={
            'Username': username,
            'Password': password,
            '__RequestVerificationToken': csrf_token,
        })

        # Check that authentication worked
        if self.session.head(BASE_URL).is_redirect:
            # Sometimes there is a page blocking here, usually the easiest step is to login manually
            # and mark it as read
            raise Exception('Error authenticating! Is there a system message blocking?')

        # Save cookies
        with open(COOKIE_PATH, 'wb') as f:
            pickle.dump(self.session.cookies, f)

    def get_current_bookings(self):
        """
        Return the current bookings for the logged in user
        """
        response = self.session.get(f'{BASE_URL}/Booking/Home/CurrentBookings')
        try:
            return response.json()['items']
        except Exception as ex:
            # Unexpected response, but still ok HTTP.
            raise Exception(response.content) from ex

    def get_available_bookings(self, teacher, start=None, end=None):
        """
        Return any available bookings within the times specified, for a given teacher id

        Args:
            teacher (int): Teacher id, probably easiest to grab from existing bookings or by
                inspecting the data on the website.
            start (datetime, optional): First time to look for available bookings. Defaults to the
                most recent Sunday.
            end (datetime, optional): Last time to look for available bookings. Defaults to 6 weeks
                from the most recent Sunday.

        Yields:
            dict: booking which is available
        """
        if not start:
            # Most recent Sunday
            start = most_recent_sunday()
        if not end:
            # Sunday 6 weeks since the most recent Sunday
            end = most_recent_sunday() + datetime.timedelta(days=7*6)
        response = self.session.post(f'{BASE_URL}/Booking/Home/Data', json={
            'Source': 'StudentCentral',
            'Person': {'id': self.person_id},
            'EducationTypeId': 3,
            'Start': f'{start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z',
            'End': f'{end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z',
            'SelectedView': 'Free',
            'ShowInListView': False,
            'TeacherIDs': [teacher]
        })
        data = response.json()

        if not data['availableTimeslots']:
            return
        yield from filter(booking_available, data['items'])
