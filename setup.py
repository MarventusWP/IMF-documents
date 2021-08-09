from setuptools import setup, find_packages

setup(
    name = "imfsearch",
    # Packaging
    packages = find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    entry_points = {
        'gui_scripts': [
            'imfsearch = imfsearch.__main__:main',
        ],
    },
)