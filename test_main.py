""" Tests for main.py """
import random
import pytest
from main import Person, dfs_draft, get_chain


class TestDraft:

    """ Draft tests """
    @pytest.fixture
    def few_restrictions(self):
        """ Returns set of Person with few restrictions """
        return {
            Person('a', restrictions=['a', 'b', 'c']),
            Person('b', restrictions=['b']),
            Person('c', restrictions=['c', 'd']),
            Person('d', restrictions=['d']),
            Person('e', restrictions=['b', 'c', 'e'])
        }

    @pytest.fixture
    def two_groups(self):
        """ Returns set of people where a single chain is not possible """
        return [
            Person('a', restrictions=['a', 'c', 'd']),
            Person('b', restrictions=['b', 'c', 'd']),
            Person('c', restrictions=['a', 'b', 'c']),
            Person('d', restrictions=['a', 'b', 'd'])
        ]

    def test_multiple_runs(self, few_restrictions):
        """ Tests multiple runs for different values of seed """
        people = few_restrictions
        for seed in range(100):
            random.seed(seed)
            drafted = dfs_draft(people)
            self.validate(drafted, people)

    def test_two_groups(self, two_groups):
        """ [WIP] Tests case where single chain is not possible """
        people = two_groups
        drafted = dfs_draft(people)
        print(get_chain(drafted))
        self.validate(drafted, people)

    @staticmethod
    def validate(drafted, people):
        """ Validates draft """
        chain = get_chain(drafted)
        # Check if there are repetitions
        assert len(set(chain)) == len(chain)
        # Check number of people in chain
        assert len(drafted) == len(people)
        # Restrictions
        for i in chain:
            assert i.secret_santa.name not in i.restrictions
