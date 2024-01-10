# Custom Packages

* `intel-oneapi-mkl`: does not provide `fftw-api@3`, so that it can be concretized together with `fftw`
    * The cuistom package can be removed in favour of `^[virtuals=blas,lapack,scalapack] intel-oneapi-mkl` when [spack/pull/35322](https://github.com/spack/spack/pull/35322) is available
