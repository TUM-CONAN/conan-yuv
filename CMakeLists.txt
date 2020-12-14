cmake_minimum_required(VERSION 2.8.12)
project(cmake_wrapper)

include(conanbuildinfo.cmake)
conan_basic_setup()

set(JPEG_ROOT ${CONAN_LIBJPEG-TURBO_ROOT})
add_subdirectory("source_subfolder")
