# Python client for STR Elevcentralen
Basic python package for looking up existing and available lesson times on [STR's Elevcentralen](https://www.elevcentralen.se/).

## Requirements
* Python 3.6+
* [Pipenv](https://github.com/pypa/pipenv)

## Installation
1. Clone the repository using: `git clone`
1. Install python environment: `pipenv install`

# Basic usage
The `ElevCentralen` class provides the basic functionality, and requires a user id. Authentication is provided by the `authenticate` method with the username and password.

## Example scripts
Can be run via `pipenv run python {SCRIPT NAME}`
### `get_current_and_available.py`
Shows of basic functionality. Grabs authentication from the environment variables (which can be easily injected via [a `.env` file](https://pipenv-fork.readthedocs.io/en/latest/advanced.html#automatic-loading-of-env)):
* `USERNAME`
* `PASSWORD`
* `PERSON_ID`
* `TEACHER_ID`

### `booking_checker.py`
Simple script to check for available new times of your favorit teacher and send out a notifying email using [mailgun](https://www.mailgun.com). Does well to run in a crontab for periodic checking of new times.
In addition to the variables above, this also requires
* `MAILGUN_URL`
* `MAILGUN_API_KEY`
* `MAILGUN_SENDER`
* `MAILGUN_RECEIVERS`: comma separated list of recipients

## Finding your user id and teacher ids
It is probably easiest to grab these from your favorite web client inspector when logged in. Another way is to
1. Login providing a dummy id
1. Get current bookings using `get_current_bookings()`
1. Grab id from one of the current bookings