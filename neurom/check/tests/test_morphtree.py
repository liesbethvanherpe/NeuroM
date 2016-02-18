# Copyright (c) 2015, Ecole Polytechnique Federale de Lausanne, Blue Brain Project
# All rights reserved.
#
# This file is part of NeuroM <https://github.com/BlueBrain/NeuroM>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#     3. Neither the name of the copyright holder nor the names of
#        its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from neurom.check import morphtree
from neurom.ezy import load_neuron
from neurom.check import morphtree as mt
from neurom.core.dataformat import COLS
from neurom.core.tree import Tree, ipreorder, val_iter
from nose import tools as nt
import numpy as np
import os

_path = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_path, '../../../test_data')
SWC_PATH = os.path.join(DATA_PATH, 'swc')

def _generate_tree(mode):

	def fake_tree(prev_radius, mode):

		if mode == 0:
			radius = prev_radius/2.
		elif mode == 1:
			radius = prev_radius
		else:
			radius = prev_radius * 2.

		return Tree(np.array([0., 0., 0., radius, 0., 0.]))

	radius = 1.

	tree = fake_tree(radius, mode)
	tree.add_child(fake_tree(tree.value[COLS.R], mode))
	tree.add_child(fake_tree(tree.value[COLS.R], mode))
	tree.children[0].add_child(fake_tree(tree.children[0].value[COLS.R], mode))
	tree.children[1].add_child(fake_tree(tree.children[1].value[COLS.R], mode))

	return tree

def _generate_zigzag_tree(n, dev):
	t = Tree(np.array([0., 0., 0., 0.2, 1., 0., 0.]))
	t.add_child(Tree(np.array([0., 1., 0., 0.15, 1., 0., 0.])))
	t.children[0].add_child(Tree(np.array([0., 2., 0., 0.14, 1., 0., 0.])))
	t.children[0].children[0].add_child(Tree(np.array([1., 3., 0., 0.15, 1., 0., 0.])))
	t.children[0].children[0].add_child(Tree(np.array([1., -3., 0., 0.15, 1., 0., 0.])))
	t.children[0].children[0].children[0].add_child(Tree(np.array([2., 4., 0., 0.11, 1., 0., 0.])))
	t.children[0].children[0].children[1].add_child(Tree(np.array([2., -4., 0., 0.12, 1., 0., 0.])))
	t.children[0].children[0].children[1].children[0].add_child(Tree(tuple(val_iter(ipreorder(t)))[n] + np.array([dev[0],dev[1],dev[2], 0.11, 1.,0.,0.])))
	t.children[0].children[0].children[1].children[0].children[0].add_child(Tree(np.array([3., -5., 0., 0.1, 1., 0., 0.])))
	t.children[0].children[0].children[1].children[0].children[0].children[0].add_child(Tree(np.array([4.,-6., 0., 0.1, 1., 0., 0.])))
	return t


def test_is_monotonic():

	# tree with decreasing radii
	decr_diams = _generate_tree(0)

	# tree with equal radii
	equl_diams = _generate_tree(1)

	# tree with increasing radii
	incr_diams = _generate_tree(2)

	nt.assert_true(mt.is_monotonic(decr_diams, 1e-6))
	nt.assert_true(mt.is_monotonic(equl_diams, 1e-6))
	nt.assert_false(mt.is_monotonic(incr_diams, 1e-6))

def test_is_flat():

	neu_tree = load_neuron(os.path.join(SWC_PATH, 'Neuron.swc')).neurites[0]

	nt.assert_false(mt.is_flat(neu_tree, 1e-6, method='tolerance'))
	nt.assert_false(mt.is_flat(neu_tree, 0.1, method='ratio'))

def test_is_zigzagging():

	# case 1: a zigzag falls directly on a previous node
	t = _generate_zigzag_tree(5, (0., 0., 0.))
	nt.assert_true(mt.is_zigzagging(t))

	# case 2: a zigzag is close to another segment
	t = _generate_zigzag_tree(5, (0.1, -0.1, 0.02))
	nt.assert_true(mt.is_zigzagging(t))

	# case 3: a zigzag is close to another segment 2
	t = _generate_zigzag_tree(5, (-0.2, 0.04, 0.144))
	nt.assert_true(mt.is_zigzagging(t))

	# case 4: a zigzag far from civilization
	t = _generate_zigzag_tree(5, (10., -10., 10.))
	nt.assert_false(mt.is_zigzagging(t))

	# case 5: a zigzag on another section
	# currently zigzag is defined on the same section
	# thus this test should not be true
	t = _generate_zigzag_tree(3, (-0.2, 0.04, 0.144))
	nt.assert_false(mt.is_zigzagging(t))