import unittest

from hypothesis import given
from hypothesis.strategies import text, integers

from pypbt import domains
from pypbt.quantifiers import forall


# --------------------------------------------------------------------------------------
# PyPBT
# --------------------------------------------------------------------------------------
@forall(x= filter(lambda x: x<20, domains.Int()))
def prop_superstupid(x):
    return x > 4


@forall(x= (a for a in domains.Int() if a<20))
def prop_superstupid_2(x):
    return x > 4


# --------------------------------------------------------------------------------------
# Unittest
# --------------------------------------------------------------------------------------
class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

    def test_that_fails(self):
        x = 0
        max([0,1])
        self.assertTrue(False)

    @unittest.skip("demonstrating skipping")
    def test_nothing(self):
        self.fail("shouldn't happen")

    @unittest.skipIf(0 < 3, "not supported in this library version")
    def test_format(self):
        # Tests that work for only a certain version of the library.
        pass

    def test_that_does_not_work(self):
        a = 1/0

    @unittest.expectedFailure
    def test_fail(self):
        self.assertEqual(1, 0, "broken")

    @unittest.expectedFailure
    def test_no_fail(self):
        self.assertEqual(1, 1, "????")


# --------------------------------------------------------------------------------------
# Hypothesis
# --------------------------------------------------------------------------------------
@given(text())
def test_simple(s):
    assert len(s) > 0


@given(integers(), integers())
def test_ints_are_commutative(x, y):
    assert x + y == y + x
