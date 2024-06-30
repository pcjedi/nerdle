import json
import os
import pickle
import string
from collections import Counter, defaultdict
from itertools import product

from tqdm import tqdm


class GuessingTree:
    guess: str | None
    possibilites: set[str]
    answers: dict[tuple[int] : "GuessingTree"]

    def __init__(self, possibilites: set[str], guess: str | None = None):
        self.possibilites = possibilites
        if guess is not None:
            self.guess = guess
        else:
            self.guess = get_next_guess(real_all_pos=possibilites, bar=False).pop()
        if len(possibilites) > 1:
            answers = defaultdict(set)
            for p in possibilites:
                answers[calc_code(secret=p, guess=self.guess)].add(p)
            answers.pop(tuple(2 for _ in self.guess))
            self.answers = {k: GuessingTree(possibilites=v) for k, v in answers.items()}


def get_next_guess(
    real_all_pos: set[str],
    vals_path: str | None = None,
    bar: bool = True,
    history: dict[str, tuple] | None = None,
) -> str:
    if history is None:
        history = {}
    new_poss = set()
    for secret in real_all_pos:
        for guess in history:
            if calc_code(secret=secret, guess=guess) != history[guess]:
                break
        else:
            new_poss.add(secret)
    if vals_path is not None:
        try:
            with open(vals_path, "br") as f:
                vals = pickle.load(f)
        except FileNotFoundError:
            vals = dict()
    else:
        vals = dict()
    for guess in tqdm(new_poss - vals.keys(), disable=not bar):
        dd = defaultdict(int)
        for secret in new_poss:
            dd[calc_code(secret=secret, guess=guess)] += 1
        vals[guess] = max(dd.values())
        if vals_path is not None:
            with open(vals_path, "+bw") as f:
                pickle.dump(vals, f)
    dd = defaultdict(set)
    for val in vals.keys() & new_poss:
        dd[vals[val]].add(val)
    return dd[min(dd)]


def calc_code(secret, guess):
    r = [0] * len(guess)
    secret_counter = Counter(secret)
    for i, l in enumerate(guess):
        if secret[i] == l:
            r[i] = 2
            secret_counter[l] -= 1
    for i, l in enumerate(guess):
        if secret[i] != l and secret_counter.get(l, 0) > 0:
            r[i] = 1
            secret_counter[l] -= 1
    return tuple(r)


def make_all_possibilities(path: str | None = None):
    if path is not None and os.path.exists(path=path):
        with open(file=path, mode="r") as f:
            return {ap for ap in json.load(fp=f)}
    operationsigns = "-+*/"
    forbiden_characters = {"".join(p) for p in product(operationsigns, repeat=2)}
    forbiden_characters |= {o + "0" for o in operationsigns}

    allposs = set()
    for llen in range(3, 6):
        for _lside in tqdm(
            desc=str(llen),
            iterable=product(operationsigns + string.digits, repeat=llen),
        ):
            for startchar in string.digits[1:]:
                lside = startchar + "".join(_lside)
                if any(sstr in lside for sstr in forbiden_characters):
                    continue
                try:
                    r = eval(lside)
                    if isinstance(r, int) and len(str(r)) + len(lside) == 7:
                        allposs.add(lside + "=" + str(r))
                except:
                    continue
    if path is not None:
        with open(path, "+w") as fp:
            json.dump(obj={ap: {} for ap in allposs}, fp=fp)
    return allposs


def flatten_guessing_tree(g: GuessingTree):
    rlist = []
    try:
        for t, g2 in g.answers.items():
            lala = [g.guess, t]
            for lblb in flatten_guessing_tree(g2):
                rlist.append(lala + lblb)
    except AttributeError:
        rlist = [[g.guess]]
    return rlist


def solution2str(solution: list[str | tuple[int]]) -> str:
    r = ""
    for s in solution:
        if isinstance(s, str):
            r += s
        elif isinstance(s, tuple):
            for i in s:
                r += str(i)
        r += ">"
    return r[:-1] + "\n"


if __name__ == "__main__":
    real_all_pos = make_all_possibilities(path="all_possibilites.json")
    g = GuessingTree(possibilites=real_all_pos, guess="48-12=36")
    fgt = flatten_guessing_tree(g)
    with open("solutions.txt", "+w") as f:
        for line in sorted(map(solution2str, fgt)):
            f.write(line)
