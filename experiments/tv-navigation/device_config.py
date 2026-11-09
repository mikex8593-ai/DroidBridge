# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
"""Explicit device selection. No discovery, default address or credential storage."""
import os

def _required(name):
    value = os.environ.get(name, '').strip()
    if not value or any(c.isspace() for c in value) or value.startswith('-'):
        raise ValueError(f'{name} must be explicitly configured')
    return value

def adb_serial():
    return _required('TV_ADB_SERIAL')

def expected_device():
    return _required('TV_EXPECTED_DEVICE')
