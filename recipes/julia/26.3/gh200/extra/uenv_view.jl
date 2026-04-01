# Author: Samuel Omlin, CSCS (omlins)   
#
# Description: Creation of an uenv view equivalent to the activation script in JUHPC.


using Pkg; Pkg.add("JSON")
using JSON


# Functions

function check_env(vars...)
    for var in vars
        if !haskey(ENV, var)
            error("uenv-view: $var is not set.")
        elseif isempty(ENV[var])
            error("uenv-view: $var is empty.")
        end
    end
end

function uenv_env(key::AbstractString)
    s = ENV[key]
    pattern = r"\$\{(.*?)\}"
    for m in eachmatch(pattern, s)
        s = replace(s, m.match => "\${@" * m.captures[1] * "@}")
    end
    return s
end


# Check if the required environment variables are set and not empty

check_env("JULIA_WRAPPER_BINDIR", "JULIAUP_WRAPPER_BINDIR", "JULIAUP_BINDIR", "JULIAUP_DEPOT", "JULIA_DEPOT", "JULIA_PREFDIR", "JULIAUP_INSTALLDIR", "ENV_JSON")


# Define the environment variables part of the juliaup view

juliaup_view_env = Dict(
    "values" => Dict(
        "list" => Dict(
            "PATH" => [
                Dict(
                    "value" => [uenv_env("JULIAUP_WRAPPER_BINDIR"), uenv_env("JULIAUP_BINDIR")], # The wrapper must be before the juliaup bindir
                    "op" => "prepend",
                ),
            ],
        ),
        "scalar" => Dict(
            "JULIAUP_DEPOT_PATH" => uenv_env("JULIAUP_DEPOT"),
            "JULIA_DEPOT_PATH"   => uenv_env("JULIA_DEPOT"),
            "JULIA_LOAD_PATH"    => ":$(uenv_env("JULIA_PREFDIR"))", # ":" means appending!
            [key => uenv_env(env_key) for (key, env_key) in 
                [("CUDA_HOME", "JUHPC_CUDA_HOME"), 
                 ("ROCM_PATH", "JUHPC_ROCM_HOME"), 
                 ("JULIA_ADIOS2_PATH", "JUHPC_ADIOS2_HOME")]
                if haskey(ENV, env_key) && !isempty(uenv_env(env_key))]..., # Conditional inclusion for variables if they are set and not empty
            [("JULIA_CUDA_MEMORY_POOL" => "none") for env_key in ["JUHPC_CUDA_HOME"] if haskey(ENV, env_key) && !isempty(uenv_env(env_key))]... # Conditionally include JULIA_CUDA_MEMORY_POOL
        )
    ),
    "version" => 1
)


# Define the environment variables part of the jupyter view

jupyter_view_env = deepcopy(juliaup_view_env)
jupyter_view_env["values"]["list"]["PATH"] = [
    Dict(
        "value" => [uenv_env("IJULIA_INSTALLER_BINDIR"), uenv_env("JULIA_WRAPPER_BINDIR"), uenv_env("JULIAUP_WRAPPER_BINDIR"), uenv_env("JULIAUP_BINDIR")], # The wrappers must be before the juliaup bindir
        "op" => "prepend",
    ),
]


# Define the juliaup view

juliaup_view = Dict(
    "juliaup" => Dict(
        "root" => "/user-environment/env/juliaup",
        "env" => juliaup_view_env,
        "activate" => "/dev/null",
        "description" => "description: HPC setup for Juliaup, Julia and some HPC key packages (Juliaup and Julia are installed on first execution of `juliaup`` in $(ENV["JULIAUP_INSTALLDIR"]))",
        "type" => "augment"
    )
)


# Define the jupyter view
jupyter_view = Dict(
    "jupyter" => Dict(
        "root" => "/user-environment/env/jupyter",
        "env" => jupyter_view_env,
        "activate" => "/dev/null",
        "description" => "description: HPC setup for Julia in Jupyter: IJulia can be installed from a Jupyter terminal by typing `install_ijulia`. The setup includes furthermore Juliaup, Julia and some HPC key packages (if not present, Juliaup and Julia are installed on first execution of `install_ijulia`/`julia`/`juliaup` in $(ENV["JULIAUP_INSTALLDIR"]))",
        "type" => "augment"
    )
)


# Merge the juliaup view with the existing views in the JSON file

env = JSON.parsefile(ENV["ENV_JSON"])
views = env["views"]
views = merge(views, juliaup_view)
views = merge(views, jupyter_view)
env["views"] = views
open(ENV["ENV_JSON"],"w") do f
    JSON.print(f, env, 4)
end


# Print the new views to the console
@info "New views:"
@info "Juliaup view:"
JSON.print(stdout, juliaup_view, 4)
@info "Jupyter view:"
JSON.print(stdout, jupyter_view, 4)


# Remove the added package
Pkg.rm("JSON")
