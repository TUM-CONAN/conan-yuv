#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.scm import Git
from conan.tools.files import load, update_conandata, copy, replace_in_file, collect_libs, get
from conans.errors import ConanInvalidConfiguration
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
            self.requires("libjpeg-turbo/2.1.5")

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
  #       tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
  #           """  target_link_libraries( yuvconvert ${JPEG_LIBRARY} )""",
  #           """  target_link_libraries( ${ly_lib_shared} ${JPEG_LIBRARY} )
  # target_link_libraries( yuvconvert ${JPEG_LIBRARY} )"""
  #           )
  #       tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
  #           """INSTALL ( PROGRAMS ${CMAKE_BINARY_DIR}/yuvconvert\t\t\tDESTINATION bin )""",
  #           """# INSTALL ( PROGRAMS ${CMAKE_BINARY_DIR}/yuvconvert\t\t\tDESTINATION bin )""",
  #           )
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

