# Copyright 2019 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# link: https://github.com/Tierion/pymerkletools/

import hashlib
from typing import Union, Iterable, ByteString


class MerkleTree:
    hash_function = hashlib.sha3_256

    def __init__(self):
        self.leaves = list()
        self.levels = None
        self.is_ready = False
        self.reset_tree()

    def reset_tree(self):
        self.leaves = list()
        self.levels = None
        self.is_ready = False

    def add_leaf(self, values: Union[Iterable[ByteString], ByteString], do_hash=False):
        self.is_ready = False
        # check if single leaf
        if not isinstance(values, Iterable):
            values = [values]

        for v in values:
            if do_hash:
                v = self.hash_function(v).digest()
            v = bytes(v)
            self.leaves.append(v)

    def get_leaf(self, index):
        return self.leaves[index]

    def get_leaf_count(self):
        return len(self.leaves)

    def get_tree_ready_state(self):
        return self.is_ready

    def _calculate_next_level(self):
        solo_leave = None
        N = len(self.levels[0])  # number of leaves on the level
        if N % 2 == 1:  # if odd number of leaves on the level
            solo_leave = self.levels[0][-1]
            N -= 1

        new_level = []
        for l, r in zip(self.levels[0][0:N:2], self.levels[0][1:N:2]):
            new_level.append(self.hash_function(l+r).digest())
        if solo_leave is not None:
            new_level.append(solo_leave)
        self.levels = [new_level, ] + self.levels  # prepend new level

    def make_tree(self):
        self.is_ready = False
        if self.get_leaf_count() > 0:
            self.levels = [self.leaves, ]
            while len(self.levels[0]) > 1:
                self._calculate_next_level()
        self.is_ready = True

    def get_merkle_root(self):
        if self.is_ready:
            if self.levels is not None:
                return self.levels[0][0]
            else:
                return None
        else:
            return None

    def get_proof(self, index):
        if self.levels is None:
            return None
        elif not self.is_ready or index > len(self.leaves)-1 or index < 0:
            return None
        else:
            proof = []
            for x in range(len(self.levels) - 1, 0, -1):
                level_len = len(self.levels[x])
                if (index == level_len - 1) and (level_len % 2 == 1):  # skip if this is an odd end node
                    index = int(index / 2.)
                    continue
                is_right_node = index % 2
                sibling_index = index - 1 if is_right_node else index + 1
                sibling_pos = "left" if is_right_node else "right"
                sibling_value = self.levels[x][sibling_index]
                proof.append({sibling_pos: sibling_value})
                index = int(index / 2.)
            return proof

    @classmethod
    def validate_proof(cls, proof, target_hash, merkle_root):
        merkle_root = bytes(merkle_root)
        target_hash = bytes(target_hash)
        if len(proof) == 0:
            return target_hash == merkle_root
        else:
            proof_hash = target_hash
            for p in proof:
                try:
                    # the sibling is a left node
                    sibling = bytes(p['left'])
                    proof_hash = cls.hash_function(sibling + proof_hash).digest()
                except KeyError:
                    # the sibling is a right node
                    sibling = bytes(p['right'])
                    proof_hash = cls.hash_function(proof_hash + sibling).digest()
            return proof_hash == merkle_root
