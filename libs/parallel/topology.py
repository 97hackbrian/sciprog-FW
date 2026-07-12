"""Cross-platform CPU topology detection and affinity utility."""

import logging
import os
from typing import Dict, List, Tuple

import psutil
from typeguard import typechecked

logger = logging.getLogger(__name__)


@typechecked
def get_topology_info() -> Tuple[List[int], List[int]]:
    """Detects CPU topology and classifies logical cores into P-Cores and E-Cores.

    It uses Linux /sys/ parsing as primary, with a fallback to psutil.
    If it cannot reliably distinguish speeds, or all cores have the same speed,
    all cores are returned as P-Cores to ensure compatibility on any x86 CPU.

    Returns:
        Tuple[List[int], List[int]]: (p_cores, e_cores) lists of logical core IDs.
    """
    total_cores = os.cpu_count() or 1
    all_cores = list(range(total_cores))

    # Try reading max frequencies from /sys/ (works reliably on Linux)
    core_freqs: Dict[int, int] = {}

    for cpu in all_cores:
        freq_path = f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/cpuinfo_max_freq"
        if os.path.exists(freq_path):
            try:
                with open(freq_path, "r") as f:
                    core_freqs[cpu] = int(f.read().strip())
            except Exception:
                pass

    if len(core_freqs) == total_cores:
        # We successfully read frequencies for all cores
        max_freq = max(core_freqs.values())
        # Define P-cores as those within 10% of the max frequency
        threshold = max_freq * 0.9

        p_cores = [c for c, f in core_freqs.items() if f >= threshold]
        e_cores = [c for c, f in core_freqs.items() if f < threshold]

        if len(p_cores) > 0:
            return p_cores, e_cores

    # Fallback 1: Try psutil (works on some Windows setups)
    try:
        freqs = psutil.cpu_freq(percpu=True)
        if freqs and len(freqs) == total_cores:
            max_freq = max(f.max for f in freqs if f.max > 0)
            if max_freq > 0:
                threshold = max_freq * 0.9
                p_cores = [i for i, f in enumerate(freqs) if f.max >= threshold]
                e_cores = [i for i, f in enumerate(freqs) if f.max < threshold]
                if len(p_cores) > 0:
                    return p_cores, e_cores
    except Exception:
        pass

    # Fallback 2: Assume homogeneous CPU (all P-Cores)
    return all_cores, []


@typechecked
def apply_pcore_affinity(all_cores: bool = False) -> None:
    """Applies CPU affinity to the current process.

    Restricts it to P-Cores unless all_cores is True or it is a homogeneous CPU.
    """
    p_cores, e_cores = get_topology_info()

    try:
        proc = psutil.Process()
        if hasattr(proc, "cpu_affinity"):
            if all_cores or not e_cores:
                # Use all available cores
                proc.cpu_affinity(p_cores + e_cores)
                logger.info(
                    f"CPU Affinity set to ALL CORES ({len(p_cores + e_cores)} logical cores)."
                )
            else:
                proc.cpu_affinity(p_cores)
                logger.info(f"CPU Affinity set strictly to P-CORES ({len(p_cores)} logical cores).")
        else:
            logger.info("CPU Affinity is not supported on this OS. Relying on default scheduler.")
    except Exception as e:
        logger.warning(f"Failed to set CPU affinity: {e}")
