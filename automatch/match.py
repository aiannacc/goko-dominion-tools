#!/usr/bin/env python

import abc
import json


class Seek:
    def __init__(self, player, reqs):
        self.player = player
        self.reqs = reqs
        self.seekid = id(self)        # TODO: ensure that this is unique


class Player:
    def __init__(self, name, rating, sets):
        self.name = name
        self.rating = rating
        self.sets = sets


class Requirement(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_valid_hosts(seeks):
        return NotImplemented


class Match:
    def __init__(self, seeks, host_name):
        self.seeks = seeks
        self.host_name = host_name
        self.accepted_by = set()
        self.matchid = id(self)        # TODO: ensure that this is unique

    def get_pnames(self):
        return [s.pname for s in self.seeks]


class Matchmaker(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate_matches(self, seeks):
        return NotImplemented


class MatchEncoder(json.JSONEncoder):
    def default(obj):
        if isinstance(obj,Match):
            out = obj.__dict__
            out.seeks = [self.default(s) for s in obj.seeks]
            return out
        elif isinstance(obj,Seek):
            out = obj.__dict__
            out.reqs = [self.default(r) for r in obj.reqs]
            return out
        elif isinstance(obj,Requirement):
            return obj.to_dict()
        else:
            return json.JSONEncoder.default(obj)
