# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
import os, unittest
from unittest.mock import patch
from device_config import adb_serial, expected_device
class Tests(unittest.TestCase):
    def test_missing_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): adb_serial()
            with self.assertRaises(ValueError): expected_device()
    def test_explicit(self):
        with patch.dict(os.environ, {'TV_ADB_SERIAL':'fixture-only','TV_EXPECTED_DEVICE':'fixture-model'}, clear=True):
            self.assertEqual(adb_serial(),'fixture-only')
            self.assertEqual(expected_device(),'fixture-model')
