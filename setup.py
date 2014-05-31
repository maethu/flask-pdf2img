from setuptools import setup

setup(
    name='flask-pdf2img',
    version='1.0',
    long_description=__doc__,
    packages=['webapp'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['pdf2img',
                      'Flask',
                      'Flask-Cache',
                      'Flask-Login',
                      'Flask-SQLAlchemy',
                      'Flask-WTF',
                      'Flask-Admin']
)
