import unittest

from AssetFundNetwork import Asset


class AssetTest  (unittest.TestCase):
    def test_set_price(self):
        asset = Asset(2, 100, 1.5, 'a1')
        asset.set_price(3)
        self.assertEqual(3, asset.price)

