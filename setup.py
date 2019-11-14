import setuptools

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import call

with open("README.md","r") as fh:
    long_description = fh.read()

class MyInstall(install):
    def run(self):
        call(["pip install -r requirements.txt --no-clean"], shell=True)
        install.run(self)

setuptools.setup(
    name="yiwise_time_regex",
    version="0.0.8",
    author="liushaoweihua",
    author_email="liushaoweihua@126.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liushaoweihua/yiwise_time_regex.git",
    include_package_data=True,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=["regex","arrow","numpy","pprint"],
    install_requires=["regex","arrow","numpy","pprint"],
    cmdclass={'install':MyInstall},
)
