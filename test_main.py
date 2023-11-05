""" Tests for main.py """
import random
import pytest
from main import Person, dfs_draw, get_chain, brute_force_draw


@pytest.fixture
def few_restrictions():
    """ Returns set of Person with few restrictions """
    return {
        Person('a', restrictions={'a', 'b', 'c'}),
        Person('b', restrictions=set()),
        Person('c', restrictions={'d'}),
        Person('d', restrictions={'d'}),
        Person('e', restrictions={'b', 'c', 'e'})
    }


@pytest.fixture
def two_groups():
    """ Returns set of people where a single chain is not possible """
    return [
        Person('a', restrictions={'a', 'c', 'd'}),
        Person('b', restrictions={'b', 'c', 'd'}),
        Person('c', restrictions={'a', 'b', 'c'}),
        Person('d', restrictions={'a', 'b', 'd'})
    ]


@pytest.mark.parametrize("algo", [dfs_draw, brute_force_draw])
def test_multiple_runs(algo, few_restrictions):
    """ Tests multiple runs for different values of seed """
    people = few_restrictions
    for seed in range(1000):
        random.seed(seed)
        drafted = algo(people)
        validate(drafted, people)


def _test_two_groups(two_groups):
    """ [WIP] Tests case where single chain is not possible """
    people = two_groups
    drafted = dfs_draw(people)
    validate(drafted, people)


def validate(drafted, people):
    """ Validates draft """
    chain = get_chain(drafted)
    # Check if there are repetitions
    assert len(set(chain)) == len(chain)
    # Check number of people in chain
    assert len(drafted) == len(people)
    # Restrictions
    for i in chain:
        assert i.secret_santa.name not in set(i.restrictions) | {i.name}
