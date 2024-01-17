"""
Meant for use in skynet. You would have to change partition names for other
SLURM clusters.
"""

import os
import sys
from typing import Any


def get_arg(args: list, choices: list, default: Any):
    for i in choices:
        if i in args:
            # Return all the other args
            remaining = args[: args.index(i)] + args[args.index(i) + 2 :]
            return args[args.index(i) + 1], remaining
    return default, args


def print_help():
    print(
        "Usage: python slurm_interactive_bash.py [options]"
        "Some helpful options:"
        "  -c, --cpus-per-task: number of cpus per task (default: 6)"
        "  -J, --job-name: name of the job (default: bash)"
        "  -C, --constraint: type of gpu (default: any)"
        "  -p, --partition: partition to use (default: overcap)"
        "  -x, --exclude: nodes to avoid (default: $BLACKLIST_NODES)"
        "  --qos: Quality of Service (default: debug)"
        "  -g, --gpu-type: type of gpu (default: any)"
    )
    exit(0)


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print_help()
    num_cpus, args = get_arg(args, ["-c", "--cpus-per-task"], 6)
    job_name, args = get_arg(args, ["-J", "--job-name"], "bash")
    partition, args = get_arg(args, ["-p", "--partition"], "overcap")
    exclude_nodes, args = get_arg(args, ["-x", "--exclude"], [])
    gpu_type, args = get_arg(args, ["-g", "--gpu-type"], "any")
    if isinstance(exclude_nodes, str):
        exclude_nodes = exclude_nodes.split(",")
    exclude_nodes += os.environ.get("BLACK_LIST_NODES", "").split(",")
    exclude_nodes = ",".join(exclude_nodes)
    gpus = f"{gpu_type}:1".replace('any:', '')

    cmd = (
        "salloc --nodes 1"
        f" --qos debug"
        f" --cpus-per-task {num_cpus}"
        f" --job-name {job_name}"
        f" --partition {partition}"
        f" --gpus {gpus}"
        f" --exclude {exclude_nodes}"
        f" {' '.join(args)}"
    )
    print("Executing:")
    print(cmd)
    os.system(cmd)


if __name__ == "__main__":
    main()
