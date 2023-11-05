"""
Secret Santa main script

TO DO:
- Simple GUI for interactive mode
- Draft for when, due to restrictions, a single chain is not possible
- Add config file with information like email subject
- Move restrictions into separate file

"""
from string import Template
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import argparse
from getpass import getpass
from typing import Set, List
from datetime import datetime


CURRENT_YEAR = datetime.now().date().strftime("%Y")
EMAIL_SUBJECT = f'Secret Santa {CURRENT_YEAR}'


def read_template(filename: str) -> Template:
    """ Reads string template from file """
    with open(filename, 'r') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def get_people(filename: str) -> Set:
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
    def __init__(self, name: str, email: str = None, gender: str = None,
                 restrictions: Set[str] = None):
        """ Constructor
        :param name: Name
        :param email: E-mail
        :param gender: Gender
        :param restrictions: Set of restrictions.
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
    def __init__(self, sender: str, msg_template: str, interactive: bool = False):
        """ Constructor
        :param sender: Sender e-mail
        :param msg_template: Message template file path
        :param interactive: Sets interactive mode
        """
        self.sender = sender
        self.interactive = interactive
        self.server = None
        self.template = read_template(msg_template)
        self.set_up()

    def set_up(self):
        """ Set up the SMTP server """
        self.server = smtplib.SMTP(host='smtp-mail.outlook.com')
        self.server.starttls()
        self.server.login(self.sender, getpass())

    def send(self, people: List[Person]):
        """ Send e-mail to each person """
        for person in people:
            print('Sending to %s (%s)' % (person.name, person.email))
            if self.interactive:
                input("Press Enter to send...")

            self._send(person)

    def _send(self, person: Person):
        """Send e-mail to person

        :param person: Person object
        """
        msg = MIMEMultipart()  # create a message

        # add in the actual person name to the message template
        message = self.template.substitute(
            PERSON_NAME=person.name,
            SECRET_SANTA=person.secret_santa.name
        )

        # set up the parameters of the message
        msg['From'] = self.sender
        msg['To'] = person.email
        msg['Subject'] = EMAIL_SUBJECT

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier.
        self.server.send_message(msg)

        del msg


def brute_force_draw(people: Set[Person]):
    valid = False
    while not valid:
        valid = _brute_force_draw(people)

    return people


def _brute_force_draw(people: Set[Person]) -> bool:
    not_selected = list(people)
    for p in people:
        ss = random.choice(not_selected)
        if ss.name in {p.name} | set(p.restrictions):
            return False
        p.set_secret_santa(ss)
        not_selected.remove(ss)

    return True


def dfs_draw(people: Set[Person]) -> Set[Person]:
    """Performs draw using an algorithm based on Depth-First Search:
    - Selects next node to visit randomly
    - Bottom node should be able to link to top node
    :param people: People to be drawn
    :return: People with secret santa attribute assigned
    """
    top = tuple(people)[0]
    # Look for chain that visits all nodes and in which bottom node can link to top
    not_selected = people.copy()
    not_selected.remove(top)
    get_secret_santa(current=top, top=top, not_selected=not_selected)

    return people


def get_chain(people: Set[Person]) -> List[Person]:
    """Returns chain of drawn people
    Assumes there is only one big chain that contains every person
    :param people: People in the chain
    :return: Chain of people where element (i) is secret santa of element (i-1)
        and first element is the secret santa of last element
    """
    chain = []
    top = tuple(people)[0]
    current = top
    while current.secret_santa != top:
        chain.append(current)
        current = current.secret_santa

    chain.append(current)

    return chain


def get_secret_santa(current: Person, top: Person, not_selected: Set[Person]):
    """Function used for secret santa DFS algorithm
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


def save_output(people: Set[Person], file_name: str):
    """ Saves draw result to file
    :param people: Set of People, with secret santa assigned
    :param file_name: Name of output file
    """
    with open(file_name, 'w') as file_obj:
        for pers in people:
            file_obj.write('%s, %s, %s, %s\n'
                           % (pers.name, pers.email, pers.gender, pers.secret_santa))


def main():
    """ Main function """
    # Parse arguments
    parser = argparse.ArgumentParser(description='Secret Santa drawer')
    parser.add_argument('data', help='File with information of each person')
    parser.add_argument('message_template', help='Path to the e-mail message template')
    parser.add_argument('--sender', help='Sender e-mail')
    parser.add_argument('--output', help='Output file to save draw results')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    args = parser.parse_args()
    # Perform draw
    people = get_people(args.data)
    # dfs_draw(people)
    brute_force_draw(people)

    if args.output is not None:
        # Save result to output file
        save_output(people, file_name=args.output)

    if args.sender is not None:
        # Send emails
        people_list = list(people)
        random.shuffle(people_list)
        msgs = Messages(
            sender=args.sender,
            msg_template=args.message_template,
            interactive=args.interactive
        )
        msgs.send(people_list)
    else:
        for p in people:
            print("%s -> %s" % (p.name, p.secret_santa.name))


if __name__ == '__main__':
    main()
