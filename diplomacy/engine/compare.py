from collections import defaultdict
from itertools import permutations

from .utils import territory, borders


def assist(T1, o1, T2, o2):
    return territory(o2['assist']) == T1

def attack_us(T1, o1, T2, o2):
    return territory(o2['target']) == T1

def attack_us_from_target(T1, o1, T2, o2):
    return (territory(o2['assist']) == territory(o1['target'])
            and territory(o2['target']) == T1)

def head_to_head(T1, o1, T2, o2, c1=False, c2=False):
    actor = o2['assist'] if o2['assist'] else o2['actor']
    T2 = territory(actor)
    if not any(territory(S) == T2 for S in borders(o1['actor'])):
        return False
    if not any(territory(S) == T1 for S in borders(actor)):
        return False
    if c1 or c2:
        return False
    return territory(o2['target']) == T1 and territory(o1['target']) == T2

def hostile_assist_hold(T1, o1, T2, o2):
    return (territory(o2['assist']) == territory(o1['target'])
            and o2['target'] is None)

def hostile_assist_compete(T1, o1, T2, o2):
    return (territory(o2['assist']) != T1 and
            territory(o2['target']) == territory(o1['target']))

def move_away(T1, o1, T2, o2):
    return (territory(o1['target']) == T2 and
            (territory(o2['target']) != T1 or o1['convoy'] or o2['convoy']))


DEPENDENCIES = {('C', 'M'): (attack_us,),
                ('S', 'C'): (attack_us,),
                ('S', 'S'): (assist, attack_us_from_target),
                ('C', 'S'): (assist,),
                ('H', 'S'): (assist, attack_us),
                ('H', 'C'): (attack_us,),
                ('M', 'S'): (assist, hostile_assist_compete,
                             head_to_head, hostile_assist_hold),
                ('M', 'C'): (assist, hostile_assist_compete),
                ('M', 'M'): (move_away,)}

def construct_dependencies(orders):
    dep = defaultdict(list)
    for (T1, o1), (T2, o2) in permutations(orders.iteritems(), 2):
        depend = False
        act1, act2 = o1['action'], o2['action']
        if (act1, act2) in DEPENDENCIES:
            depend = any(f(T1, o1, T2, o2) for f in DEPENDENCIES[(act1, act2)])

        if depend:
            dep[T1].append(T2)

    return dep
