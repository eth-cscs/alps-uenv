system_specific_scalar_env = [
    "NCCL_NET" => "AWS Libfabric",
    "NCCL_NET_GDR_LEVEL" => "PHB",
    "NCCL_CROSS_NIC" => "1",
    "NCCL_PROTO" => "^LL128",
    "FI_CXI_DEFAULT_CQ_SIZE" => "131072",
    "FI_CXI_DEFAULT_TX_SIZE" => "16384",
    "FI_CXI_DISABLE_HOST_REGISTER" => "1",
    "FI_CXI_RX_MATCH_MODE" => "software",
    "FI_MR_CACHE_MONITOR" => "userfaultfd",
]