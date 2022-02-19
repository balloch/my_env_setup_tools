import argparse
import itertools
import os.path as osp

from sbatch_glob import sbatch_all


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sbatch_file")
    parser.add_argument("parameters", nargs="+")
    parser.add_argument("-g", "--generate-only", action="store_true")
    parser.add_argument("-t", "--template-name")
    parser.add_argument("-a", "--auto-name")
    args = parser.parse_args()
    if args.auto_name is not None:
        params = args.auto_name.split(",")
        params_str = "_".join([f"{p}${idx+1}" for idx, p in enumerate(params)])
        grandparent_dir = osp.basename(
            osp.dirname(osp.dirname(osp.abspath(args.sbatch_file)))
        )
        args.template_name = f"{grandparent_dir}_{params_str}.sh"
    run(**vars(args))


def run(
    sbatch_file,
    parameters,
    generate_only=False,
    template_name=None,
    **kwargs,
):
    assert osp.isfile(sbatch_file), f"{sbatch_file} does not exist!"
    if template_name is not None:
        assert template_name.endswith(".sh")
    sbatch_file = osp.abspath(sbatch_file)

    # Get data from template slurm file
    with open(sbatch_file) as f:
        template_data = f.read()

    # Get every possible permutation of values to sweep over
    permutations = itertools.product(*[i.split(",") for i in parameters])
    sbatch_files = []
    for p_idx, p in enumerate(permutations):
        print("permutation: ", p)
        # Generate name for new file
        src_dir = osp.dirname(sbatch_file)
        if template_name is None:
            out_name = "_".join([sbatch_file[:-3], *p, ".sh"])
        else:
            out_name = template_name
            for idx, arg in enumerate(p):
                out_name = out_name.replace(f"${idx + 1}", arg)
            out_name = osp.join(src_dir, out_name)

        # Fill in $ values in template with permutation, where $0 is the name of the
        # file being generated with no extension
        data = template_data
        for idx, arg in enumerate(p):
            data = data.replace(f"${idx+1}", arg)
        out_name_no_ext, _ = osp.splitext(out_name)
        out_name_no_ext_base = osp.basename(out_name_no_ext)
        data = data.replace("$BASE_NAME", out_name_no_ext_base)
        data = data.replace("$FULL_NAME", out_name_no_ext)
        data = data.replace("$SRC_DIR", src_dir)

        # Add paths for output and error if they don't exist in template. They will
        # be saved to the same folder as the template file with the same name as the
        # generated sbatch file (with correct extension). Also add job name.
        extra_params = []
        if "#SBATCH --job-name" not in data:
            job_name = osp.basename(osp.splitext(out_name)[0])
            extra_params.append(f"#SBATCH --job-name={job_name}")
        if "#SBATCH --output" not in data:
            extra_params.append(f"#SBATCH --output={out_name[:-3] + '.out'}")
        if "#SBATCH --error" not in data:
            extra_params.append(f"#SBATCH --error={out_name[:-3] + '.err'}")
        if extra_params:
            data_lines = data.splitlines()
            data_lines = [data_lines[0], *extra_params, *data_lines[1:]]
            data = "\n".join(data_lines) + "\n"

        with open(out_name, "w") as f:
            f.write(data)

        # Queue file for execution
        sbatch_files.append(out_name)

    if not generate_only:
        sbatch_all(sbatch_files)


if __name__ == "__main__":
    main()
