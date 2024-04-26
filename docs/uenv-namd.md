# NAMD

[NAMD] is a parallel molecular dynamics code based on [Charm++] designed for high-performance simulation of large biomolecular systems.

!!! danger "Licensing Terms and Conditions"
    
    [NAMD] is distributed free of charge for research purposes only and not for commercial use: users must agree to [NAMD license] in order to use it at [CSCS]. Users agree to acknowledge use of [NAMD] in any reports or publications of results obtained with the Software (see [NAMD Homepage] for details).

!!! warning

    Currently, we only provide single-GPU and single-node multi-GPU [NAMD] builds, which greatly benefit from the new GPU-resident mode providing very fast dynamics (see [NAME 3.0 new features]). If you require a multi-node version of [NAMD], please contact us.

## Useful Links

* [NAMD Spack package]
* [NAMD Tutorials]
* [Charm++ Spack package]
* [Running Charm++ Programs]
* [What you should know about NAMD and Charm++ but were hoping to ignore] by J. C. Phillips

[Charm++]: https://charm.cs.uiuc.edu/ 
[Charm++ Spack package]: https://packages.spack.io/package.html?name=charmpp 
[CSCS]: https://www.cscs.ch
[NAMD]: http://www.ks.uiuc.edu/Research/namd/
[NAMD Homepage]: http://www.ks.uiuc.edu/Research/namd/
[NAMD license]: http://www.ks.uiuc.edu/Research/namd/license.html
[NAMD Tutorials]: http://www.ks.uiuc.edu/Training/Tutorials/index.html#namd
[NAMD Spack package]: https://packages.spack.io/package.html?name=namd
[Running Charm++ Programs]: https://charm.readthedocs.io/en/latest/charm++/manual.html#running-charm-programs
[What you should know about NAMD and Charm++ but were hoping to ignore]: https://dl.acm.org/doi/pdf/10.1145/3219104.3219134
[NAMD 3.0 new features]: https://www.ks.uiuc.edu/Research/namd/3.0/features.html
