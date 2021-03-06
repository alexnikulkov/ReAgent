#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All rights reserved.

import logging
from typing import List


logger = logging.getLogger(__name__)


class Trainer:
    def __init__(self, minibatch_size: int):
        self.reporter = None
        self.minibatch_size = minibatch_size

    def train(self, training_batch) -> None:
        raise NotImplementedError()

    def state_dict(self):
        return {c: getattr(self, c).state_dict() for c in self.warm_start_components()}

    def load_state_dict(self, state_dict):
        for c in self.warm_start_components():
            getattr(self, c).load_state_dict(state_dict[c])

    def warm_start_components(self) -> List[str]:
        """
        The trainer should specify what members to save and load
        """
        raise NotImplementedError
