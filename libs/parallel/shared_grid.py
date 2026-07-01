"""Shared memory buffer management for multiprocessing."""

from multiprocessing.shared_memory import SharedMemory

import numpy as np
from typeguard import typechecked


@typechecked
class SharedGridBuffer:
    """Manages two shared memory blocks (current and next) for double-buffered computing."""

    def __init__(self, shape: tuple[int, int], name_prefix: str = "gol_"):
        self.shape = shape
        self.size_bytes = shape[0] * shape[1]

        self.current_shm = SharedMemory(create=True, size=self.size_bytes)
        self.next_shm = SharedMemory(create=True, size=self.size_bytes)

        # NumPy views wrapping the shared memory
        self.current_array = np.ndarray(self.shape, dtype=np.uint8, buffer=self.current_shm.buf)
        self.next_array = np.ndarray(self.shape, dtype=np.uint8, buffer=self.next_shm.buf)

    def swap(self) -> None:
        """Swap the roles of the current and next buffers."""
        # Swap underlying shared memory objects
        self.current_shm, self.next_shm = self.next_shm, self.current_shm
        # Swap numpy array views
        self.current_array, self.next_array = self.next_array, self.current_array

    def load(self, data: np.ndarray) -> None:
        """Load data into the current buffer."""
        np.copyto(self.current_array, data)

    def close(self) -> None:
        """Close the local views of the shared memory."""
        self.current_shm.close()
        self.next_shm.close()

    def unlink(self) -> None:
        """Destroy the shared memory segments (call in owning process ONLY)."""
        self.current_shm.unlink()
        self.next_shm.unlink()

    def __enter__(self) -> "SharedGridBuffer":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
        self.unlink()
