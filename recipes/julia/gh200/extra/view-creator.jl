using JSON

# if !haskey(ENV, "DO_INSTALL_VIEW") error("DO_INSTALL_VIEW not set") end

    julia_view_env = Dict(
        "values" => Dict(
            "list" => Dict(
                "PATH" => Dict(
                    "value" => [ENV["JULIAUP_WRAPPER_BINDIR"], ENV["JULIAUP_BINDIR"]],
                    "op" => "prepend",
                ),
                "JULIAUP_DEPOT_PATH" => Dict(
                    "value" => [ENV["JULIAUP_DEPOT"]],
                    "op" => "append",
                ),
                "JULIA_DEPOT_PATH" => Dict(
                    "value" => [ENV["JULIA_DEPOT"]],
                    "op" => "append",
                ),
                "JULIA_LOAD_PATH" => Dict(
                    "value" => [ENV["JULIA_PREFDIR"]],
                    "op" => "append",
                ),
            ),
            "scalar" => Dict(
                "JULIA_ADIOS2_PATH" => ENV["JULIA_ADIOS2_PATH"]
            )
        ),
        "version" => 1
    )

    julia_view = Dict(
        "julia" => Dict(
            "root" => "/user-environment/env/julia",
            "env" => julia_view_env,
            "activate" => "/dev/null",
            "description" => "provide juliaup and julia (installed on first execution of juliaup on $(ENV["JULIAUP_ROOTDIR"]))",
            "type" => "augment"
        )
    )

    env = JSON.parsefile(ENV["ENV_JSON"])
    views = env["views"]
    # default_view = views["default"]
    # default_view_env = default_view["env"]
    # default_view_env_values = default_view_env["values"]
    # default_view_env_values_list = default_view_env_values["list"]
    # default_view_env_values_scalar = default_view_env_values["scalar"]
    views = merge(views, julia_view)
    env["views"] = views    
    open(ENV["ENV_JSON"],"w") do f
        JSON.print(f, env, 4)
    end

    # open("test.json","w") do f
    #     JSON.print(f, env, 4)
    # end


#     install_view_env = Dict(
#         "values" => Dict(
#             "list" => Dict(
#                 "PATH" => Dict(
#                     "value" => [ENV["JULIAUP_WRAPPER_BINDIR"]],
#                     "op" => "prepend",
#             )
#         ),
#         "version" => 1
#     )

#     install_view = Dict(
#         "install" => Dict(
#             "root" => "/user-environment/env/install",
#             "env" => install_view_env,
#             "activate" => "/user-environment/env/install/activate.sh",
#             "description" => "View for the installation of juliaup (plus the latest version of julia) on $(ENV[JULIAUP_ROOTDIR]): execute `juliaup`",
#             "type" => "spack-view"
#         )
#     )
# # end


# if ENV["DO_INSTALL_VIEW"]
#     @info "Create install view"
#     create_install_view()
# else
#     @info "Create run view"
#     create_run_view()