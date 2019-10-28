#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Secret Santa main script

usage: main.py [-h] [--sender SENDER] [--output OUTPUT] [--interactive] data

TO DO:
- Simple GUI for interactive mode
- Draft for when, due to restrictions, a single chain is not possible
- Add config file with information like email subject

"""
from string import Template
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import argparse
from getpass import getpass


EMAIL_SUBJECT = 'Secret Santa'
MESSAGE_TEMPLATE = 'message.txt'


def read_template(filename):
    """ Reads string template from file """
    with open(filename, 'r') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def get_people(filename):
    """ Function to read the contacts from a given contact file and return a list of names and
    email addresses """
    people = set()
    with open(filename, mode='r') as contacts_file:
        for a_contact in contacts_file:
            name, email, gender, restrictions = [col.strip() for col in a_contact.split(',')]
            restrictions = set(restrictions.split(';') + [name])
            if '' in restrictions:
                restrictions.remove('')
            people.add(Person(name=name, email=email, gender=gender, restrictions=restrictions))

    return people


class Person:
    """ Person class """
    def __init__(self, name, email=None, gender=None, restrictions=None):
        """ Constructor
        :param name: str
            Name
        :param email: str or None
            E-mail
        :param gender: str or None
            Gender
        :param restrictions: (list of str) or None
            List of restrictions.
            If None, it is set to empty list
        """
        self.name = name
        self.email = email
        self.gender = gender
        self.restrictions = restrictions if restrictions is not None else []
        self._secret_santa = None

    @property
    def secret_santa(self):
        """ Returns secret santa Person object"""
        return self._secret_santa

    def set_secret_santa(self, secret_santa):
        """ Sets secret santa
        :param secret_santa: Person
            Secret santa object
        """
        self._secret_santa = secret_santa

    def __str__(self):
        """ Returns name str """
        return self.name


class Messages:
    """ Messages class
    Handles sending of messages by e-mail """
    def __init__(self, sender, interactive=False):
        """
        Constructor
        :param sender: str
            Sender e-mail
        :param interactive: bool
            Sets interactive mode
        """
        self.sender = sender
        self.interactive = interactive
        self.server = None
        self.template = read_template(MESSAGE_TEMPLATE)
        self.set_up()

    def set_up(self):
        """ Set up the SMTP server """
        self.server = smtplib.SMTP(host='smtp-mail.outlook.com')
        self.server.starttls()
        self.server.login(self.sender, getpass())

    def send(self, people):
        """ Send e-mail to each person """
        for person in people:
            print('Sending to %s (%s)' % (person.name, person.email))
            if self.interactive:
                input("Press Enter to send...")

            self._send(person)

    def _send(self, person):
        """
        Send e-mail to person
        :param person: Person
            Person object
        """
        msg = MIMEMultipart()  # create a message

        # add in the actual person name to the message template
        message = self.template.substitute(
            PERSON_NAME=person.name,
            SECRET_SANTA=person.secret_santa.name
        )

        # setup the parameters of the message
        msg['From'] = self.sender
        msg['To'] = person.email
        msg['Subject'] = EMAIL_SUBJECT

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier.
        self.server.send_message(msg)

        del msg


def dfs_draw(people):
    """
    Performs draw using an algorithm based on Depth-First Search:
    - Selects next node to visit randomly
    - Bottom node should be able to link to top node
    :param people: set of Person
        People to be drawed
    :return: set of Person
        People with secret santa attribute assigned
    """
    top = tuple(people)[0]
    # Look for chain that visits all nodes and in which bottom node can link to top
    not_selected = people.copy()
    not_selected.remove(top)
    get_secret_santa(current=top, top=top, not_selected=not_selected)

    return people


def get_chain(people):
    """
    Returns chain of drawed people
    Assumes there is only one big chain that contains every person
    :param people: set of Person
        People in the chain
    :return: list of Person
        Chain of people where element (i) is secret santa of element (i-1) and first element is the
        secret santa of last element
    """
    chain = []
    top = tuple(people)[0]
    current = top
    while current.secret_santa != top:
        chain.append(current)
        current = current.secret_santa

    chain.append(current)

    return chain


def get_secret_santa(current, top, not_selected):
    """
    Function used for secret santa DFS algorithm
    :param current: Person
        Current node
    :param top: Person
        Top node
    :param not_selected: set of Person
        Set of "not selected so far" people
    :return: Person or None
        Person with secret santa assigned or None in case it is not possible to assign someone
    """
    if not not_selected and top.name not in current.restrictions:
        # We are at the end of the chain and top element can be assigned to current
        current.set_secret_santa(top)
        return current

    possibilities = [i for i in not_selected if i.name not in current.restrictions]
    random.shuffle(possibilities)
    for pers in possibilities:
        next_not_selected = not_selected.copy()
        next_not_selected.remove(pers)
        secret_santa = get_secret_santa(current=pers, top=top, not_selected=next_not_selected)
        if secret_santa is not None:
            current.set_secret_santa(secret_santa)
            return current

    return None


def save_output(people, file_name):
    """
    Saves draw result to file
    :param people: set of People
        Set of People, with secret santa assigned
    :param file_name: str
        Name of output file
    """
    with open(file_name, 'w') as file_obj:
        for pers in people:
            file_obj.write('%s, %s, %s, %s\n'
                           % (pers.name, pers.email, pers.gender, pers.secret_santa))


def send_messages(people, sender, interactive=False):
    """ Send messages to e-mails """
    msgs = Messages(sender=sender, interactive=interactive)
    msgs.send(people)


def main():
    """ Main function """
    # Parse arguments
    parser = argparse.ArgumentParser(description='Secret Santa drawer')
    parser.add_argument('data', help='File with information of each person')
    parser.add_argument('--sender', help='Sender e-mail')
    parser.add_argument('--output', help='Output file to save draw results')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    args = parser.parse_args()
    # Perform draw
    people = get_people(args.data)
    dfs_draw(people)

    if args.output is not None:
        # Save result to output file
        save_output(people, file_name=args.output)

    if args.sender is not None:
        # Send emails
        people_list = list(people)
        random.shuffle(people_list)
        send_messages(people_list, sender=args.sender, interactive=args.interactive)
    else:
        print([i.name for i in get_chain(people)])


if __name__ == '__main__':
    main()
