from setuptools import find_packages, setup

setup(
    name="old.addon",
    version="1.2.3",
    description="A legacy Plone add-on (mr.bob era)",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["old"],
    install_requires=["setuptools", "Products.CMFPlone"],
)
