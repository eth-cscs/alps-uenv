
message("CMAKE_CURRENT_LIST_DIR = ${CMAKE_CURRENT_LIST_DIR}")
message("OUTPUT_DIR             = ${OUTPUT_DIR}")
message("UENV_IMAGE             = ${UENV_IMAGE}")
message("PARAVIEW_INSTALL_DIR   = ${PARAVIEW_INSTALL_DIR}")
message("PARAVIEW_PLUGINS_DIR   = ${PARAVIEW_PLUGINS_DIR}")
message("PV_LIBRARY_PATH        = ${PV_LIBRARY_PATH}")

# perform string substitution on the rc-submit-pvserver.sh script
configure_file(
    ${CMAKE_CURRENT_LIST_DIR}/rc-submit-pvserver.sh.cmake
    ${OUTPUT_DIR}/rc-submit-pvserver.sh
    FILE_PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    @ONLY)

# perform string substitution on the gpu_wrapper.sh script
configure_file(
    ${CMAKE_CURRENT_LIST_DIR}/gpu_wrapper.sh.cmake
    ${OUTPUT_DIR}/gpu_wrapper.sh
    FILE_PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    @ONLY)
