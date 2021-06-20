import os
import pickle

import requests

from elevcentralen import ElevCentralen as EC
from elevcentralen import check_ok, cleanup_booking

CACHE = os.environ.get('BOOKING_CHECKER_CACHE_PATH')
if not CACHE:
    CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.booking_checker_cache')
MAILGUN_URL = 'https://api.mailgun.net/v3/{}/messages'.format(os.environ['MAILGUN_URL'])


def send_email(subject, body):
    """
    Send email using Mailgun using settings from environment variables
    """
    requests.post(
        MAILGUN_URL,
        auth=('api', os.environ['MAILGUN_API_KEY']),
        data={
            'from': f"Automagic Körskole Checker <{os.environ['MAILGUN_SENDER']}>",
            'to': os.environ['MAILGUN_RECEIVERS'].split(' '),
            'subject': subject,
            'text': body
        },
        hooks={'response': check_ok}
    )


def email_error():
    """
    Grab the traceback of the current exception and send it as an email to the admin of the script
    """
    import traceback
    requests.post(
        MAILGUN_URL,
        auth=('api', os.environ['MAILGUN_API_KEY']),
        data={
            'from': f"Automagic Körskole Checker <{os.environ['MAILGUN_SENDER']}>",
            'to': os.environ['MAILGUN_SENDER'],
            'subject': 'Python Exception',
            'text': 'An exception occured:\n' + traceback.format_exc()
        },
        hooks={'response': check_ok}
    )


def get_bookings(ec):
    """
    Find new bookings, return grouped by if they are on new days, or days with bookings on them
    already

    Args:
        ec (ElevCentralen): Authenticated elevcentralen client to query for bookings

    Returns:
        list, list: Bookings on previously unbooked days, and booked days, respectively
    """
    current_dates = {
        booking['start'].date()
        for booking in map(cleanup_booking, ec.get_current_bookings())
    }
    unbooked_days = []
    previously_booked_days = []

    for booking in map(cleanup_booking, ec.get_available_bookings(os.environ['TEACHER_ID'])):
        if booking['start'].date() in current_dates:
            previously_booked_days.append(booking)
        else:
            unbooked_days.append(booking)
    return unbooked_days, previously_booked_days


def main():
    """
    Check for new bookings, and send email if new times have popped up since script was last run
    """
    e = EC(os.environ['PERSON_ID'])
    e.authenticate(os.environ['USERNAME'], os.environ['PASSWORD'])
    unbooked_days, previously_booked_days = get_bookings(e)
    print(f'Found {len(previously_booked_days)} new times on existing days and {len(unbooked_days)}'
          ' on new days')
    try:
        with open(CACHE, 'br') as f:
            prev_notified_times = pickle.load(f)
    except (IOError, EOFError):
        # File didn't exist or was not pickled
        prev_notified_times = []

    if all(b in prev_notified_times for b in previously_booked_days + unbooked_days):
        # Nothign to update
        print('No new times which are not yet notified')
        return

    previous_days_str = '\n'.join(
        f'{b["teacher"]}: {b["start"]:%Y-%m-%d %H:%M} - {b["end"]:%H:%M}'
        for b in previously_booked_days
    )
    new_days_str = '\n'.join(
        f'{b["teacher"]}: {b["start"]:%Y-%m-%d %H:%M} - {b["end"]:%H:%M}'
        for b in unbooked_days
    )

    send_email('New available appointments',
               f'New driving days are available:\n{new_days_str}\n\n'
               f'New times are available:\n{previous_days_str}')
    with open(CACHE, 'bw') as f:
        pickle.dump(previously_booked_days + unbooked_days, f)


if __name__ == '__main__':
    try:
        main()
    except:
        email_error()
        raise
