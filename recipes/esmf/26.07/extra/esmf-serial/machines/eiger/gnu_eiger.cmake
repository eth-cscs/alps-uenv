# work around strict compiler warnings in gfortran 10 and later
string(APPEND FFLAGS " -fallow-argument-mismatch -fallow-invalid-boz")
if (compile_threaded)
  string(APPEND FFLAGS " -qopenmp")
endif()

# help CESM find lapack
string(APPEND SLIBS " -L/user-environment/env/esmf/lib -lopenblas")

