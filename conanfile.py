#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.scm import Git
from conan.tools.files import load, update_conandata, copy, replace_in_file, collect_libs, get, rm
from conan.errors import ConanInvalidConfiguration
import os


class LibnameConan(ConanFile):
    name = "yuv"
    version = "1749"

    description =   "a C++ libary to parse yuv files."
    # topics can get used for searches, GitHub topics, Bintray tags etc. Add here keywords about the library
    topics = ("conan", "corrad", "magnum", "filesystem", "console", "environment", "os")
    url = "https://github.com/TUM-CONAN/conan-yuv"
    homepage = "https://github.com/ulricheck/libyuv"
    author = "ulrich eck"
    license = "MIT"  # Indicates license type of the packaged library; please use SPDX Identifiers https://spdx.org/licenses/

    exports = ["CMakeLists.txt", "LICENSE.md"]
    # exports_sources = ["CMakeLists.txt", "patches/*"]

    # Options may need to change depending on the packaged library.
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False], 
        "fPIC": [True, False],
        "with_jpeg": [False, "libjpeg", "libjpeg-turbo"],
    }
    default_options = {
        "shared": False, 
        "fPIC": True,
        "with_jpeg": "libjpeg",
    }


    def requirements(self):
        if self.options.with_jpeg == "libjpeg":
            self.requires("libjpeg/9d")
        elif self.options.with_jpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/3.0.0")

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
        # if str(self.options.with_jpeg) == "libjpeg-turbo":
        #     raise ConanInvalidConfiguration(
        #         "libjpeg-turbo is an invalid option right now, as it is not supported by the cmake script.")

    def configure(self):
        if self.options.shared and self.options.with_jpeg == "libjpeg-turbo":
            self.options["libjpeg-turbo"].shared = True


    def export(self):
        update_conandata(self, {"sources": {
            "commit": "v{}".format(self.version),
            "url": "https://github.com/ulricheck/libyuv.git"
        }})

    def source(self):
        git = Git(self)
        sources = self.conan_data["sources"]
        git.clone(url=sources["url"], target=self.source_folder, args=["--recursive", ])
        git.checkout(commit=sources["commit"])

    def generate(self):
        tc = CMakeToolchain(self)

        def add_cmake_option(option, value):
            var_name = "{}".format(option).upper()
            value_str = "{}".format(value)
            var_value = "ON" if value_str == 'True' else "OFF" if value_str == 'False' else value_str
            tc.variables[var_name] = var_value

        for option, value in self.options.items():
            add_cmake_option(option, value)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()


    def layout(self):
        cmake_layout(self, src_folder="source_folder")

    def build(self):        
        if self.settings.os == 'Windows':
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                """  target_link_libraries( yuvconvert ${JPEG_LIBRARY} )""",
                """  target_link_libraries(${ly_lib_shared} ${JPEG_INCLUDE_DIR}/../lib/jpeg.lib)
  target_link_libraries( yuvconvert ${JPEG_LIBRARY} )"""
                )
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                """INSTALL ( PROGRAMS ${CMAKE_BINARY_DIR}/yuvconvert\t\t\tDESTINATION bin )""",
                """# INSTALL ( PROGRAMS ${CMAKE_BINARY_DIR}/yuvconvert\t\t\tDESTINATION bin )""",
                )
                
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        # Upstream CMakeLists always builds AND installs both the static (libyuv.a)
        # and shared (libyuv.so) libraries. Shipping both in a single package is
        # ambiguous: on Linux CMakeDeps' find_library() resolves "yuv" to the .so
        # first (default suffix order .so;.a), so a STATIC consumer ends up with a
        # STATIC imported target whose IMPORTED_LOCATION points at libyuv.so. When
        # the linker is put into -Bstatic mode this fails with
        # "attempted static link of dynamic object libyuv.so".
        # Keep only the library that matches the `shared` option. On Windows the
        # static lib and the DLL import lib share the .lib extension, so they can't
        # be told apart here; only clean up on Unix where .a vs .so/.dylib is
        # unambiguous.
        if self.settings.os != "Windows":
            libdir = os.path.join(self.package_folder, "lib")
            if self.options.shared:
                rm(self, "*.a", libdir)
            else:
                rm(self, "*.so*", libdir)
                rm(self, "*.dylib", libdir)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

