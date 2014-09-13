from setuptools import setup  # noqa

setup(name='yalpt',
      version='0.1.0',
      description='Yet Another Literate Python Tool',
      long_description=open('README.md').read(),
      scripts=['run-lit.py'],
      author='Solly Ross',
      author_email='sross@redhat.com',
      license='ISC and PSF',
      url='https://github.com/directxman12/yalpt',
      packages=['yalpt'],
      install_requires=['six'],
      keywords='literate documentation tutorial',
      classifiers=[
        'Developement Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Documentation',
        'Topic :: Software Development',
        'License :: OSI Approved :: ISC License (ISCL)',
        'License :: OSI Approved :: Python Software Foundation License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
      ])