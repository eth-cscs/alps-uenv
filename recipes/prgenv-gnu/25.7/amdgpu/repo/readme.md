`llvm-amdgpu` built during the compiler stage isn't reused in the main environment, try injecting a hardcoded dependency to python@3.13.8 into the package.py (same version as used in the uenv later)
