# Author: Samuel Omlin, CSCS (omlins)   
#
# Description: Creation of an uenv view equivalent to the activation script in JUHPC.


using Pkg; Pkg.add("JSON")
using JSON


# Check if the required environment variables are set

function check_env(vars...)
    for var in vars
        if !haskey(ENV, var)
            error("uenv-view: $var is not set.")
        elseif isempty(ENV[var])
            error("uenv-view: $var is empty.")
        end
    end
end

check_env("JULIAUP_WRAPPER_BINDIR", "JULIAUP_BINDIR", "JULIAUP_DEPOT", "JULIA_DEPOT", "JULIA_PREFDIR", "JULIAUP_INSTALLDIR", "ENV_JSON")


# Define the environment variables part of the julia view

julia_view_env = Dict(
    "values" => Dict(
        "list" => Dict(
            "PATH" => [
                Dict(
                    "value" => [ENV["JULIAUP_WRAPPER_BINDIR"], ENV["JULIAUP_BINDIR"]], # The wrapper must be before the juliaup bindir
                    "op" => "prepend",
                ),
            ],
        ),
        "scalar" => Dict(
            "JULIAUP_DEPOT_PATH" => ENV["JULIAUP_DEPOT"],
            "JULIA_DEPOT_PATH"   => ENV["JULIA_DEPOT"],
            "JULIA_LOAD_PATH"    => ":$(ENV["JULIA_PREFDIR"])", # ":" means appending!
            [key => ENV[env_key] for (key, env_key) in 
                [("CUDA_HOME", "JUHPC_CUDA_HOME"), 
                 ("ROCM_PATH", "JUHPC_ROCM_HOME"), 
                 ("JULIA_ADIOS2_PATH", "JUHPC_ADIOS2_HOME")]
                if haskey(ENV, env_key) && !isempty(ENV[env_key])]..., # Conditional inclusion for variables if they are set and not empty
            [("JULIA_CUDA_MEMORY_POOL" => "none") for env_key in ["JUHPC_CUDA_HOME"] if haskey(ENV, env_key) && !isempty(ENV[env_key])]... # Conditionally include JULIA_CUDA_MEMORY_POOL
        )
    ),
    "version" => 1
)


# Define the julia view

julia_view = Dict(
    "julia" => Dict(
        "root" => "/user-environment/env/julia",
        "env" => julia_view_env,
        "activate" => "/dev/null",
        "description" => "description: HPC setup for juliaup, julia and some HPC key packages (juliaup and julia are installed on first execution of juliaup in $(ENV["JULIAUP_INSTALLDIR"]))",
        "type" => "augment"
    )
)


# Merge the julia view with the existing views in the JSON file

env = JSON.parsefile(ENV["ENV_JSON"])
views = env["views"]
views = merge(views, julia_view)
env["views"] = views
open(ENV["ENV_JSON"],"w") do f
    JSON.print(f, env, 4)
end


# Remove the added package
Pkg.rm("JSON")