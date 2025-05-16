# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyPsutil(PythonPackage):
    """psutil is a cross-platform library for retrieving information on
    running processes and system utilization (CPU, memory, disks, network)
    in Python."""

    homepage = "https://github.com/giampaolo/psutil"
    pypi = "psutil/psutil-5.6.3.tar.gz"

    license("BSD-3-Clause")

    version("7.0.0", sha256="7be9c3eba38beccb6495ea33afd982a44074b78f28c434a1f51cc07fd315c456")
    version("6.1.1", sha256="cf8496728c18f2d0b45198f06895be52f36611711746b7f30c464b422b50e2f5")
    version("6.1.0", sha256="353815f59a7f64cdaca1c0307ee13558a0512f6db064e92fe833784f08539c7a")
    version("6.0.0", sha256="8faae4f310b6d969fa26ca0545338b21f73c6b15db7c4a8d934a5482faa818f2")
    version("5.9.8", sha256="6be126e3225486dff286a8fb9a06246a5253f4c7c53b475ea5f5ac934e64194c")
    version("5.9.7", sha256="3f02134e82cfb5d089fddf20bb2e03fd5cd52395321d1c8458a9e58500ff417c")
    version("5.9.6", sha256="e4b92ddcd7dd4cdd3f900180ea1e104932c7bce234fb88976e2a3b296441225a")
    version("5.9.5", sha256="5410638e4df39c54d957fc51ce03048acd8e6d60abc0f5107af51e5fb566eb3c")
    version("5.9.4", sha256="3d7f9739eb435d4b1338944abe23f49584bde5395f27487d2ee25ad9a8774a62")
    version("5.9.2", sha256="feb861a10b6c3bb00701063b37e4afc754f8217f0f09c42280586bd6ac712b5c")
    version("5.8.0", sha256="0c9ccb99ab76025f2f0bbecf341d4656e9c1351db8cc8a03ccd62e318ab4b5c6")
    version("5.7.2", sha256="90990af1c3c67195c44c9a889184f84f5b2320dce3ee3acbd054e3ba0b4a7beb")
    version("5.6.3", sha256="863a85c1c0a5103a12c05a35e59d336e1d665747e531256e061213e2e90f63f3")
    version("5.6.2", sha256="828e1c3ca6756c54ac00f1427fdac8b12e21b8a068c3bb9b631a1734cada25ed")
    version("5.5.1", sha256="72cebfaa422b7978a1d3632b65ff734a34c6b34f4578b68a5c204d633756b810")
    version("5.4.5", sha256="ebe293be36bb24b95cdefc5131635496e88b17fabbcf1e4bc9b5c01f5e489cfe")
    version("5.0.1", sha256="9d8b7f8353a2b2eb6eb7271d42ec99d0d264a9338a37be46424d56b4e473b39e")

    depends_on("c", type="build")  # generated

    # pyproject.toml
    depends_on("py-setuptools@43:", when="@5.9.4:", type="build")
    depends_on("py-setuptools", type="build")
