
# perform string substitution on the rc-submit-pvserver.sh script

configure_file(
    ${INPUT_FILE_NAME}
    ${OUTPUT_FILE_NAME}
    FILE_PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    @ONLY)

message("Written ${OUTPUT_FILE_NAME}")
