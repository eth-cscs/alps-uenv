from spack_repo.builtin.packages.libfabric.package import Libfabric as BuiltinLibfabric

from spack.package import *

class Libfabric(BuiltinLibfabric):
    # This patches missing synchronization for GPU-GPU transfers in the lnx
    # provider of libfabric. The patch is from from a comment on the
    # corresponding issue:
    # https://github.com/ofiwg/libfabric/issues/11231#issue-3252163450.
    #
    # It's unclear if this is a good patch, but it's sufficient for testing of
    # the lnx provider. If and when the correct fix is published the patch can
    # be backported on the upstream libfabric package.
    #
    # The patch may not apply for all versions (tested with 2.3.1), but there
    # is no version constraint as the patch is essential. Builds should fail if
    # the patch doesn't apply.
    # patch("issue-11231-cuda-sync.patch", when="fabrics=lnx")
    pass
