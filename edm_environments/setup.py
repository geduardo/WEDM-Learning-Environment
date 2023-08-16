from setuptools import setup, find_packages

setup(
    name="edm_environments",
    version="0.0.1",
    packages=find_packages(include=['envs*', 'wrappers*']),
    install_requires=["gymnasium==0.29.0", "pygame==2.1.0"],
)