
message("CMAKE_CURRENT_LIST_DIR = ${CMAKE_CURRENT_LIST_DIR}")
message("OUTPUT_DIR = ${OUTPUT_DIR}")
message("UENV = ${UENV}")

# perform string substitution on the rc-submit-pvserver.sh script
# requires the OUTPUT_DIR variable to be set as well as VARS that are used in the script
configure_file(
    ${CMAKE_CURRENT_LIST_DIR}/rc-submit-pvserver.sh.cmake
    ${OUTPUT_DIR}/rc-submit-pvserver.sh 
    FILE_PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE       
    @ONLY)
