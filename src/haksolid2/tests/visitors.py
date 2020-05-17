from .. import transform
from ..math import *
from .common import *
from .. import usability
import unittest


class VisitorTest(unittest.TestCase):
	def test_allAbsTransforms(self):

		a = transform.translate(10)
		b = transform.translate(0, -10)
		c = transform.translate(0, 10)
		d = transform.translate(z=10)

		e = transform.translate(z=-5)
		f = transform.translate(-5)

		g = transform.translate(0, 0, 0)

		transform.translate(666) * transform.untransform() * transform.translate(
		  12) * g

		a * b * d
		a * c * d

		d * e * g
		f * g

		v = usability.AllAbsTransformsVisitor()

		g.visitAncestors(v)

		matrices_expected = (
		  M.Translation(V(-5, 0, 0)),
		  M.Translation(V(12, 0, 0)),
		  M.Translation(V(10, -10, 5)),
		  M.Translation(V(10, 10, 5))
		)

		for T in v.absTransforms:
			found = 0
			for T1 in matrices_expected:
				if (abs(T - T1) <= 1e-2).all():
					found += 1
			self.assertEqual(found, 1)
