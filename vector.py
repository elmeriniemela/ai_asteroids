from math import sqrt


def plus(list1, list2):
    a = [list1[0] + list2[0], list1[1] + list2[1]]
    return a


def dotp(list1, list2):
    a = list1[0] * list2[0] + list1[1] * list2[1]
    return a


def times(scalar, list1):
    a = [x * scalar for x in list1]
    return a


def reverse(list1):
    a = [-list1[0], -list1[1]]
    return a


def mag(list1):
    a = sqrt(dotp(list1, list1))
    return a


def proj(list1, list2):
    scalar = dotp(list1, list2) / dotp(list2, list2)
    a = times(scalar, list2)
    return a


def comp(list1, list2):
    a = dotp(list1, list2) / mag(list2)
    return a

def unit(list):
    scalar = mag(list)
    a = times(1/scalar, list)
    return a
