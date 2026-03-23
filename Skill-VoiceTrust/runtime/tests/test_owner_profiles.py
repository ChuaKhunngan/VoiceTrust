"""Tests for owner profile aggregation in the self-contained runtime."""
from pathlib import Path
import sys
import numpy as np
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data.owner_profiles import OwnerProfileStore


def test_owner_profile_append_and_aggregate():
    with tempfile.TemporaryDirectory() as tmp:
        store = OwnerProfileStore(Path(tmp))
        p1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        p2 = np.array([3.0, 4.0, 5.0], dtype=np.float32)

        profile1 = store.append_sample("owner", "a.wav", p1)
        assert len(profile1.samples) == 1

        profile2 = store.append_sample("owner", "b.wav", p2)
        assert len(profile2.samples) == 2

        agg = np.load(store.aggregate_path("owner"))
        assert np.allclose(agg, np.array([2.0, 3.0, 4.0], dtype=np.float32))
