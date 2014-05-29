from setuptools import setup

setup(
    name='pdf2img',
    version='1.0',
    long_description=__doc__,
    packages=['pdf2img', 'web'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask',
                      'Flask-Cache',
                      'Flask-Login',
                      'Flask-SQLAlchemy',
                      'Flask-WTF',
                      'Flask-Admin']
)
