from elevcentralen import ElevCentralen, cleanup_booking
import os


def main():
    e = ElevCentralen(os.environ['PERSON_ID'])
    e.authenticate(os.environ['USERNAME'], os.environ['PASSWORD'])
    for b in map(cleanup_booking, e.get_current_bookings()):
        print(f'Booked ({b["teacher"]}): {b["start"]}-{b["end"]}')

    for b in map(cleanup_booking, e.get_available_bookings(os.environ['TEACHER_ID'])):
        print(f'Available ({b["teacher"]}): {b["start"]}-{b["end"]}')


if __name__ == '__main__':
    main()
