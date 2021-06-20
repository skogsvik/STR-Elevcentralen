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

## Finding your user id and teacher ids
It is probably easiest to grab these from your favorite web client inspector when logged in. Another way is to
1. Login providing a dummy id
1. Get current bookings using `get_current_bookings()`
1. Grab id from one of the current bookings